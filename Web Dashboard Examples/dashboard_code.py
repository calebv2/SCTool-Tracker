# routes

import asyncio
import hashlib
import json
import os
import random
import re
import sqlite3
import uuid
from datetime import datetime, timezone
import redis
import requests
import time
from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from packaging import version
from extensions import limiter, logger, csrf
from flask_socketio import SocketIO

from .forms import (
    get_db,
    close_db,
    register_teardown_callbacks,
    process_all_wrapper,
    process_all,
    parse_actor_death_event,
    add_column_if_not_exists,
    validate_api_key,
    is_version_valid,
    require_api_key,
    log_db_interaction,
    throttle_requests,
    process_kill_data,
    get_username_by_id,
    check_rsi_bio,
    process_death_data
)

from .random import (
    redis_client,
    GAME_MODES,
    PATCH_DATES
)

socketio = SocketIO(message_queue="redis://", async_mode="threading")

api_bp = Blueprint('api', __name__)
csrf.exempt(api_bp)
web_bp = Blueprint('web', __name__)

web_bp.record_once(register_teardown_callbacks)

# Define a default image URL to use when no player image is provided.
DEFAULT_IMAGE_URL = "https://cdn.robertsspaceindustries.com/static/images/account/avatar_default_big.jpg"

class DeleteKillForm(FlaskForm):
    pass

class BulkDeleteForm(FlaskForm):
    pass

@api_bp.route('/ping', methods=['GET'])
@require_api_key
def ping():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT in_game_name FROM user_profiles WHERE discord_id = ?", (g.user_id,))
    row = cursor.fetchone()
    if row:
        return jsonify({'message': 'pong', 'registered_in_game_name': row['in_game_name']}), 200
    else:
        return jsonify({'error': 'Player not registered'}), 400

@api_bp.route('/player_kills/<int:author_id>', methods=['GET'])
def get_player_kills(author_id):
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    per_page = 50
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM kills WHERE author_id = ?", (author_id,))
    total_kills = cursor.fetchone()['count']
    total_pages = (total_kills + per_page - 1) // per_page
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages if total_pages > 0 else 1
    cursor.execute("""
        SELECT id, guild_id, author_id, player_name, victim_engagement, attacker_engagement, timestamp, clip_url, game_mode, player_image, method
        FROM kills
        WHERE author_id = ?
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """, (author_id, per_page, offset))
    kills = cursor.fetchall()
    kills_list = [{
        'id': kill['id'],
        'guild_id': kill['guild_id'],
        'author_id': kill['author_id'],
        'player_name': kill['player_name'],
        'victim_engagement': kill['victim_engagement'],
        'attacker_engagement': kill['attacker_engagement'],
        'timestamp': kill['timestamp'],
        'clip_url': kill['clip_url'],
        'game_mode': kill['game_mode']
    } for kill in kills]
    pagination = {
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'current_page': page,
        'total_pages': total_pages
    }
    return jsonify({
        'kills': kills_list,
        'pagination': pagination,
        'total_kills': total_kills
    })

@api_bp.route('/latest_version', methods=['GET'])
def get_latest_version():
    latest_version = get_version_from_file()
    return jsonify({'latest_version': latest_version}), 200

@api_bp.route('/test_redis', methods=['GET'])
def test_redis_connection():
    """
    Test endpoint to verify Redis connection is working properly.
    Returns the Redis ping response and connection status.
    """
    try:
        # Test basic Redis connection
        ping_response = redis_client.ping()
        
        # Test publish functionality
        test_message = {"test": "message", "timestamp": datetime.now().isoformat()}
        pub_result = redis_client.publish("test_channel", json.dumps(test_message))
        
        # Test Socket.IO connection
        socketio_status = "Connected" if socketio.server.manager.redis_client else "Not connected"
        
        return jsonify({
            'status': 'success',
            'redis_ping': ping_response,
            'redis_publish': bool(pub_result),
            'socketio_status': socketio_status,
            'message': 'Redis connection is working properly'
        }), 200
    except Exception as e:
        logger.exception("Redis connection test failed: %s", e)
        return jsonify({
            'status': 'error',
            'message': f'Redis connection test failed: {str(e)}'
        }), 500

@web_bp.route('/personal_kills')
def personal_kills():
    if 'user_id' not in session:
        flash("Please log in to view your personal kills.", "warning")
        return redirect(url_for('login'))
    user_id = session['user_id']
    guild_id = session.get('guild_id')
    if not guild_id:
        flash("No guild selected.", "error")
        return redirect(url_for('pick_server'))
    patch_dates = PATCH_DATES
    patch = request.args.get('patch', 'ALL')
    if patch != 'ALL' and patch not in patch_dates:
        flash("Invalid patch specified.", "error")
        return redirect(url_for('pick_server'))
    if patch == 'ALL':
        start_date = "1950-01-01 00:00:00"
        end_date = "2030-01-01 00:00:00"
    else:
        start_date, end_date = patch_dates[patch]
    search_query = request.args.get('search_query', '').strip()
    game_mode = request.args.get('game_mode', None)
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    per_page = 50
    offset = (page - 1) * per_page
    db = get_db()
    cursor = db.cursor()
    query_conditions = ["k.author_id = ?", "datetime(k.timestamp) BETWEEN ? AND ?"]
    params = [user_id, start_date, end_date]
    if search_query:
        query_conditions.append("LOWER(k.player_name) LIKE ?")
        params.append(f"%{search_query.lower()}%")
    if game_mode:
        query_conditions.append("k.game_mode = ?")
        params.append(game_mode)
    where_clause = " AND ".join(query_conditions)
    aggregator_query = f"""
        SELECT 
            k.player_name,
            k.victim_engagement,
            k.attacker_engagement
        FROM kills k
        WHERE {where_clause}
    """
    cursor.execute(aggregator_query, params)
    all_kill_rows = cursor.fetchall()
    ship_regex = re.compile(
        r"\b(?:Aegis|Anvil|Aopoa|Argo|Banu|C\.O\.|Crusader|Drake|Esperia|Gatac|Greycat|Kruger|Mirai|MISC|Origin|RSI|Tumbril|Vanduul)\b",
        re.IGNORECASE
    )
    attacker_ship_counts = {}
    victim_ship_counts = {}
    fps_weapon_counts = {}
    for row in all_kill_rows:
        attacker_eng = row['attacker_engagement'] or ""
        victim_eng = row['victim_engagement'] or ""
        if " using " in attacker_eng:
            parts = attacker_eng.split(" using ", 1)
            possible_ship = parts[0].strip()
            weapon_part = parts[1].strip()
            if possible_ship.lower() in ["vehicle destruction", "player destruction"]:
                attacker_ship = None
                fps_weapon = weapon_part
            else:
                if ship_regex.search(possible_ship):
                    attacker_ship = possible_ship
                else:
                    attacker_ship = None
                fps_weapon = weapon_part
        else:
            attacker_ship = None
            fps_weapon = attacker_eng.strip()
        if ship_regex.search(victim_eng):
            victim_ship = victim_eng.strip()
        else:
            victim_ship = None
        if attacker_ship:
            attacker_ship_counts[attacker_ship] = attacker_ship_counts.get(attacker_ship, 0) + 1
        else:
            weapon = fps_weapon.strip()
            if weapon:
                fps_weapon_counts[weapon] = fps_weapon_counts.get(weapon, 0) + 1
        if victim_ship:
            victim_ship_counts[victim_ship] = victim_ship_counts.get(victim_ship, 0) + 1
    favorite_attacker_ship = (
        max(attacker_ship_counts.items(), key=lambda x: x[1])[0] if attacker_ship_counts else "N/A"
    )
    most_ship_killed = (
        max(victim_ship_counts.items(), key=lambda x: x[1])[0] if victim_ship_counts else "N/A"
    )
    favorite_fps_weapon = (
        max(fps_weapon_counts.items(), key=lambda x: x[1])[0] if fps_weapon_counts else "N/A"
    )
    base_query = f"""
        SELECT 
            k.id, k.player_name, k.victim_engagement, k.attacker_engagement, 
            k.timestamp, k.clip_url, k.game_mode, k.player_image,
            p.enlistment_date, p.occupation, p.org_name, p.org_tag
        FROM kills k
        LEFT JOIN player_info p ON LOWER(k.player_name) = LOWER(p.player_name)
        WHERE {where_clause}
        ORDER BY datetime(k.timestamp) DESC
        LIMIT ? OFFSET ?
    """
    params_extended = params + [per_page, offset]
    count_query = f"SELECT COUNT(*) as count FROM kills k WHERE {where_clause}"
    cursor.execute(count_query, params)
    total_kills = cursor.fetchone()['count']
    total_pages = (total_kills + per_page - 1) // per_page
    if page < 1:
        page = 1
    elif page > total_pages:
        page = max(total_pages, 1)
    cursor.execute(base_query, params_extended)
    rows = cursor.fetchall()
    kills_list = []
    for row in rows:
        attacker_eng = row['attacker_engagement'] or ""
        victim_eng = row['victim_engagement'] or ""
        if " using " in attacker_eng:
            parts = attacker_eng.split(" using ", 1)
            possible_ship = parts[0].strip()
            weapon_part = parts[1].strip()
            if possible_ship.lower() in ["vehicle destruction", "player destruction"]:
                attacker_ship = None
                fps_weapon = weapon_part
            else:
                if ship_regex.search(possible_ship):
                    attacker_ship = possible_ship
                else:
                    attacker_ship = None
                fps_weapon = weapon_part
        else:
            attacker_ship = None
            fps_weapon = attacker_eng.strip()
        if ship_regex.search(victim_eng):
            victim_ship = victim_eng.strip()
        else:
            victim_ship = None
        if victim_ship:
            destruction_type = "Vehicle destruction"
        else:
            destruction_type = "Player destruction"
        kill_record = {
            'id': row['id'],
            'player_name': row['player_name'],
            'victim_engagement': row['victim_engagement'],
            'attacker_engagement': row['attacker_engagement'],
            'timestamp': row['timestamp'],
            'clip_url': row['clip_url'],
            'game_mode': row['game_mode'],
            'player_image': row['player_image'],
            'enlistment_date': row['enlistment_date'],
            'occupation': row['occupation'],
            'org_name': row['org_name'],
            'org_tag': row['org_tag'],
            'attacker_ship': attacker_ship,
            'victim_ship': victim_ship,
            'fps_weapon': fps_weapon,
            'destruction_type': destruction_type
        }
        kills_list.append(kill_record)
    in_game_name = None
    try:
        cursor.execute("SELECT in_game_name FROM user_profiles WHERE discord_id = ?", (user_id,))
        user_profile = cursor.fetchone()
        in_game_name = user_profile['in_game_name'] if user_profile else None
    except Exception as e:
        logger.error("Error retrieving user profile: %s", e)
    try:
        top_victims_query = """
            SELECT player_name, COUNT(*) as kill_count
            FROM kills
            WHERE author_id = ? AND datetime(timestamp) BETWEEN ? AND ?
            GROUP BY player_name
            ORDER BY kill_count DESC
            LIMIT 4
        """
        cursor.execute(top_victims_query, (user_id, start_date, end_date))
        top_victims_data = cursor.fetchall()
        top_victims = [{
            'player_name': row[0],
            'kill_count': row[1]
        } for row in top_victims_data]
    except Exception as e:
        logger.error("Database error while fetching top victims: %s", e)
        top_victims = []
    # Create pagination object that matches the expected format in the template
    pagination = {
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'current_page': page,
        'total_pages': total_pages,
        'per_page': per_page,
        'pages': list(range(1, total_pages + 1))
    }
    return render_template(
        'personal_kills.html',
        kills=kills_list,
        pagination=pagination,
        total_kills=total_kills,
        search_query=search_query,
        patch=patch,
        game_mode=game_mode,
        patches=list(patch_dates.keys()),
        game_modes=[
            "Team Elimination", "PU", "Gun Rush", "Tonk Royale", "Free Flight",
            "Squadron Battle", "Vehicle Kill Confirmed", "FPS Kill Confirmed",
            "Control", "Duel"
        ],
        guild_id=guild_id,
        in_game_name=in_game_name,
        top_victims=top_victims,
        favorite_attacker_ship=favorite_attacker_ship,
        most_ship_killed=most_ship_killed,
        favorite_fps_weapon=favorite_fps_weapon
    )

@web_bp.route('/delete_kills', methods=['POST'])
def delete_kills():
    form = BulkDeleteForm()
    if not form.validate_on_submit():
        flash("CSRF token is missing or invalid.", "error")
        return redirect(url_for('web.personal_kills'))
    if 'user_id' not in session:
        flash("Please log in to delete kills.", "warning")
        return redirect(url_for('login'))
    user_id = session['user_id']
    kill_ids = request.form.getlist('kill_ids')
    if not kill_ids:
        flash("No kills selected for deletion.", "warning")
        return redirect(url_for('web.personal_kills'))
    db = get_db()
    cursor = db.cursor()
    try:
        placeholders = ','.join('?' for _ in kill_ids)
        query = f"DELETE FROM kills WHERE id IN ({placeholders}) AND author_id = ?"
        params = kill_ids + [user_id]
        cursor.execute(query, params)
        
        # Use the retry mechanism for database commit
        retry_on_db_lock(lambda: db.commit())
        
        flash(f"Deleted {cursor.rowcount} kill(s) successfully.", "success")
    except Exception as e:
        logger.error("Error deleting kills: %s", e)
        flash("Error deleting selected kills.", "error")
    return redirect(url_for('web.personal_kills'))

@api_bp.route('/kills', methods=['POST'])
@require_api_key
@throttle_requests(max_requests=5000, time_window=60)
@limiter.limit("1000 per minute")
def add_kill():
    if g.client_id == 'kill_logger_client':
        is_valid, error_message = is_version_valid(g.client_version)
        if not is_valid:
            logger.warning("Version check failed for user_id: %s, error: %s", g.user_id, error_message)
            return jsonify({'error': error_message}), 426

    try:
        user_id = g.user_id
        guild_id = g.guild_id
        data = request.get_json()
        if not data:
            logger.warning("Invalid JSON data from user_id: %s", user_id)
            return jsonify({'error': 'Invalid JSON data'}), 400

        kills = []
        npc_skip_count = 0

        # Process data whether it's a list or single record.
        if isinstance(data, list):
            for kill_data in data:
                kill_record = process_kill_data(kill_data, user_id)
                if not kill_record:
                    continue

                # Skip records flagged as NPC, self-kill, or suicide.
                if (kill_record.get('npc_skip') or 
                    kill_record.get('self_kill_skip') or 
                    kill_record.get('suicide_skip')):
                    npc_skip_count += 1
                    continue

                # Only add records that have the expected 'player_name' key.
                if 'player_name' not in kill_record:
                    continue
                kills.append(kill_record)
        else:
            kill_record = process_kill_data(data, user_id)
            if kill_record:
                if (kill_record.get('npc_skip') or 
                    kill_record.get('self_kill_skip') or 
                    kill_record.get('suicide_skip')):
                    npc_skip_count += 1
                elif 'player_name' in kill_record:
                    kills.append(kill_record)

        if not kills:
            if npc_skip_count > 0:
                logger.info("All kills were NPC/self-kills; nothing was logged.")
                return jsonify({'message': 'All NPC/self-kill events skipped; nothing was logged.'}), 200
            else:
                return jsonify({'error': 'No valid kill records found'}), 400

        db = get_db()
        cursor = db.cursor()
        previous_changes = db.total_changes

        insert_query = """
            INSERT OR IGNORE INTO kills (
                id, guild_id, author_id,
                player_name, victim_engagement,
                attacker_engagement, timestamp,
                clip_url, game_mode, player_image, method
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params_list = []
        for record in kills:
            # Attempt to parse timestamps that might include fractional seconds and a trailing 'Z'
            try:
                raw_ts = record['timestamp']
                # Replace trailing 'Z' with '+00:00' for fromisoformat compatibility
                if raw_ts.endswith('Z'):
                    raw_ts = raw_ts[:-1] + '+00:00'
                dt = datetime.fromisoformat(raw_ts)
                # Preserve microseconds:
                record_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            except Exception as e:
                logger.warning("Failed to parse timestamp '%s': %s", record['timestamp'], e)
                # Fallback to the raw value if parsing fails
                record_timestamp = record['timestamp']

            duplicate_query = """
                SELECT id FROM kills
                WHERE author_id = ? 
                  AND player_name = ? 
                  AND timestamp = ?
            """
            cursor.execute(duplicate_query, (user_id, record['player_name'].lower(), record_timestamp))
            if cursor.fetchone():
                logger.info(
                    "Duplicate kill for %s at %s found. Skipping...",
                    record['player_name'], record_timestamp
                )
                continue

            params_list.append((
                str(uuid.uuid4()),
                guild_id,
                user_id,
                record['player_name'].lower(),
                record['victim_engagement'],
                record['attacker_engagement'],
                record_timestamp,
                record['clip_url'],
                record['game_mode'],
                record.get('player_image', DEFAULT_IMAGE_URL),
                record.get('method')  # Destruction method/weapon type
            ))

        cursor.executemany(insert_query, params_list)
        
        # Use the retry mechanism for database commit
        def commit_operation():
            db.commit()
            return db.total_changes - previous_changes
            
        inserted_count = retry_on_db_lock(commit_operation)

        if inserted_count == 0:
            logger.info("All kills were duplicates; returning 201 to avoid client retry loops.")
            return jsonify({'message': "Duplicate kill. This can't be logged."}), 201

        # Start the asynchronous player info update in the background.
        try:
            socketio.start_background_task(process_all_wrapper, kills)
        except Exception as e:
            logger.error("Error processing player info: %s", e)

        # Give time for background tasks before data enrichment
        time.sleep(1)

        # Enrich each record with additional player info.
        for record in kills:
            cursor.execute(
                """
                SELECT enlistment_date, occupation, org_name, org_tag
                FROM player_info
                WHERE LOWER(player_name)=?
                """,
                (record['player_name'].lower(),)
            )
            player_info = cursor.fetchone()
            if player_info:
                record['enlistment_date'] = player_info['enlistment_date']
                record['occupation'] = player_info['occupation']
                record['org_name'] = player_info['org_name']
                record['org_tag'] = player_info['org_tag']
            else:
                # Fallback values if no record exists.
                record['enlistment_date'] = "No enlistment date"
                record['occupation'] = "No occupation"
                record['org_name'] = "No org"
                record['org_tag'] = "No tag"

            # Notify each kill with enriched data.
            for rec in kills:
                notification_payload = {
                    "guild_id": guild_id,
                    "author_id": user_id,
                    "player_name": rec['player_name'],
                    "victim_engagement": rec['victim_engagement'],
                    "attacker_engagement": rec['attacker_engagement'],
                    "timestamp": rec['timestamp'],
                    "clip_url": rec['clip_url'],
                    "game_mode": rec['game_mode'],
                    "enlistment_date": rec.get("enlistment_date"),
                    "occupation": rec.get("occupation"),
                    "org_name": rec.get("org_name"),
                    "org_tag": rec.get("org_tag"),
                    "method": rec.get("method")
                }
                try:
                    socketio.emit("new_kill", notification_payload)
                    redis_client.publish("kill_notifications", json.dumps(notification_payload))
                except Exception as e:
                    logger.error("Failed to publish kill notification: %s", e)

        return jsonify({
            'message': f'{inserted_count} kill record(s) added successfully. '
                       f'NPC/self-kill events skipped: {npc_skip_count}'
        }), 201

    except Exception as e:
        logger.exception("An error occurred in add_kill route: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@web_bp.app_template_filter('time_ago')
def time_ago_filter(date_str):
    if not date_str:
        return ""
    try:
        created_time = datetime.fromisoformat(date_str)
    except ValueError:
        try:
            created_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return date_str
    now = datetime.now(timezone.utc).astimezone(created_time.tzinfo) if created_time.tzinfo else datetime.now()
    diff = now - created_time
    days = diff.days
    seconds = diff.seconds
    if days < 0:
        return "just now"
    if days == 0:
        hours = seconds // 3600
        if hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        minutes = seconds // 60
        if minutes > 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        return "just now"
    if days < 7:
        return f"{days} day{'s' if days > 1 else ''} ago"
    weeks = days // 7
    if weeks < 5:
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months > 1 else ''} ago"
    years = days // 365
    return f"{years} year{'s' if years > 1 else ''} ago"

def initialize_api_keys_table(db):
    """Create the api_keys table if it doesn't exist."""
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            api_key_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            UNIQUE(user_id, guild_id, api_key_hash)
        )
    ''')
    db.commit()
    logger.info("API keys table initialized")
    return True

@web_bp.route('/manage_api_keys', methods=['GET', 'POST'])
def manage_api_keys():
    if 'user_id' not in session:
        return redirect(url_for('login', next=url_for('web.manage_api_keys')))
    user_id = session['user_id']
    guild_id = session.get('guild_id')
    if not guild_id:
        # Store the current destination in session to redirect back after server selection
        session['next_after_guild_selection'] = url_for('web.manage_api_keys')
        flash("Please select a server first.")
        return redirect(url_for('server_selection'))
    db = get_db()
    
    # Initialize the api_keys table if it doesn't exist
    try:
        initialize_api_keys_table(db)
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize API keys table: {e}")
        flash("An error occurred while setting up API key management.", "error")
        return redirect(url_for('server_selection'))
    
    cursor = db.cursor()
    
    # Add id column to api_keys table if it doesn't exist
    try:
        cursor.execute("SELECT id FROM api_keys LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cursor.execute("ALTER TABLE api_keys ADD COLUMN id TEXT")
            # Update existing rows with UUIDs
            cursor.execute("SELECT api_key_hash FROM api_keys WHERE id IS NULL")
            rows = cursor.fetchall()
            for row in rows:
                key_hash = row['api_key_hash']
                new_id = str(uuid.uuid4())
                cursor.execute("UPDATE api_keys SET id = ? WHERE api_key_hash = ?", (new_id, key_hash))
            db.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to modify api_keys table: {e}")
    
    if 'verification_codes' not in session:
        session['verification_codes'] = {}
        
    if request.method == 'POST':
        if 'generate_key' in request.form:
            api_key = os.urandom(24).hex()
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            created_at = datetime.utcnow().isoformat()
            try:
                cursor.execute("""
                    INSERT INTO api_keys (id, user_id, guild_id, api_key_hash, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (str(uuid.uuid4()), user_id, guild_id, api_key_hash, created_at))
                
                # Use the retry mechanism for database commit
                retry_on_db_lock(lambda: db.commit())
                
                session['new_api_key'] = api_key
                flash('API key generated successfully.', 'success')
            except sqlite3.Error as e:
                logger.error("Database error during API key generation: %s", e)
                flash('An error occurred while generating the API key.', 'error')
            return redirect(url_for('web.manage_api_keys'))
        elif 'revoke_key' in request.form:
            api_key_hash = request.form.get('api_key_hash')
            if not api_key_hash:
                flash('API key hash is required to revoke a key.', 'error')
                return redirect(url_for('web.manage_api_keys'))
            try:
                cursor.execute("""
                    UPDATE api_keys
                    SET is_active = 0
                    WHERE user_id = ? AND guild_id = ? AND api_key_hash = ?
                """, (user_id, guild_id, api_key_hash))
                
                # Use the retry mechanism for database commit
                retry_on_db_lock(lambda: db.commit())
                
                flash('API key revoked successfully.', 'success')
            except sqlite3.Error as e:
                logger.error("Database error during API key revocation: %s", e)
                flash('An error occurred while revoking the API key.', 'error')
            return redirect(url_for('web.manage_api_keys'))
        elif 'start_verification' in request.form:
            in_game_name = request.form.get('in_game_name').strip()
            if not in_game_name:
                flash('Please enter a valid in-game name.', 'error')
                return redirect(url_for('web.manage_api_keys'))
            verification_code = ''.join(random.choices('0123456789', k=20))
            session['verification_codes'][str(user_id)] = {
                'code': verification_code,
                'in_game_name': in_game_name
            }
            session.modified = True
            flash('Verification code generated. Please add it to your RSI profile bio.', 'info')
            return redirect(url_for('web.manage_api_keys'))
        elif 'verify_code' in request.form:
            user_verification = session['verification_codes'].get(str(user_id))
            if not user_verification:
                flash('No verification process found. Please start verification first.', 'error')
                return redirect(url_for('web.manage_api_keys'))
            in_game_name = user_verification['in_game_name']
            verification_code = user_verification['code']
            bio_check = check_rsi_bio(in_game_name, verification_code)
            if bio_check:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_profiles (discord_id, in_game_name)
                        VALUES (?, ?)
                    """, (user_id, in_game_name))
                    db.commit()
                    del session['verification_codes'][str(user_id)]
                    session.modified = True
                    flash('Verification successful! You are now verified.', 'success')
                except sqlite3.Error as e:
                    logger.error("Database error during verification: %s", e)
                    flash('An error occurred while verifying your in-game name.', 'error')
                return redirect(url_for('web.manage_api_keys'))
            else:
                flash('Verification failed. Please ensure the code is in your RSI bio and try again.', 'error')
                return redirect(url_for('web.manage_api_keys'))
        elif 'reverify_confirm' in request.form:
            try:
                cursor.execute("DELETE FROM user_profiles WHERE discord_id = ?", (user_id,))
                db.commit()
                session['verification_codes'].pop(str(user_id), None)
                flash("Your account has been unverified. Please verify your account with your new in-game name.", "info")
            except sqlite3.Error as e:
                logger.error("Database error during re-verification: %s", e)
                flash("An error occurred during re-verification.", "error")
            return redirect(url_for('web.manage_api_keys'))
        else:
            flash('Invalid action.', 'error')
            return redirect(url_for('web.manage_api_keys'))
    else:
        cursor.execute("""
            SELECT api_key_hash, created_at
            FROM api_keys
            WHERE user_id = ? AND guild_id = ? AND is_active = 1
        """, (user_id, guild_id))
        api_keys = cursor.fetchall()
        active_key_count = len(api_keys)
        cursor.execute("SELECT in_game_name FROM user_profiles WHERE discord_id = ?", (user_id,))
        user_profile = cursor.fetchone()
        is_verified = user_profile is not None
        in_game_name = user_profile['in_game_name'] if is_verified else None
        user_verification = session['verification_codes'].get(str(user_id))
        verification_code = user_verification['code'] if user_verification else None
        api_key = session.pop('new_api_key', None)
        return render_template(
            'manage_api_keys.html',
            active_key_count=active_key_count,
            api_key=api_key,
            api_keys=api_keys,
            guild_id=guild_id,
            is_verified=is_verified,
            in_game_name=in_game_name,
            verification_code=verification_code
        )

@web_bp.route('/kill_leaderboard')
def kill_leaderboard():
    guild_id = session.get('guild_id')
    if not guild_id:
        flash("Please select a server first.")
        return redirect(url_for('server_selection'))
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    selected_game_mode = request.args.get('game_mode', None)
    selected_patch = request.args.get('patch', 'ALL')
    patch_dates = PATCH_DATES
    if selected_patch != 'ALL' and selected_patch not in patch_dates:
        flash("Invalid patch specified.", "error")
        return redirect(url_for('server_selection'))
    if selected_patch == 'ALL':
        start_date = "1950-01-01 00:00:00"
        end_date = "2030-01-01 00:00:00"
    else:
        start_date, end_date = patch_dates[selected_patch]
    per_page = 50
    offset = (page - 1) * per_page
    allowed_game_modes = [
        "Team Elimination", "Elimination", "PU", "Gun Rush", "Tonk Royale", "Free Flight",
        "Squadron Battle", "Vehicle Kill Confirmed", "FPS Kill Confirmed",
        "Control", "Duel"
    ]
    db = get_db()
    cursor = db.cursor()
    
    # Calculate overall statistics for analytics dashboard
    analytics_query = """
        SELECT COUNT(*) as total_kills_count
        FROM kills 
        WHERE datetime(timestamp) BETWEEN ? AND ?
    """
    analytics_params = [start_date, end_date]
    
    if selected_game_mode:
        analytics_query += " AND game_mode = ?"
        analytics_params.append(selected_game_mode)
        
    cursor.execute(analytics_query, analytics_params)
    total_kills_count = cursor.fetchone()['total_kills_count']
    
    # Count active players (players who have made kills)
    active_players_query = """
        SELECT COUNT(DISTINCT author_id) as active_players_count
        FROM kills
        WHERE datetime(timestamp) BETWEEN ? AND ?
    """
    active_players_params = [start_date, end_date]
    
    if selected_game_mode:
        active_players_query += " AND game_mode = ?"
        active_players_params.append(selected_game_mode)
        
    cursor.execute(active_players_query, active_players_params)
    active_players_count = cursor.fetchone()['active_players_count']
    
    # Get kill method statistics
    method_query = """
        SELECT method, COUNT(*) as count
        FROM kills
        WHERE datetime(timestamp) BETWEEN ? AND ?
    """
    method_params = [start_date, end_date]
    
    if selected_game_mode:
        method_query += " AND game_mode = ?"
        method_params.append(selected_game_mode)
        
    method_query += " GROUP BY method ORDER BY count DESC"
    cursor.execute(method_query, method_params)
    method_stats = cursor.fetchall()
    
    # Set default values in case no methods are found
    top_method = "Unknown"
    method_percentage = 0
    
    if method_stats and len(method_stats) > 0:
        top_method = method_stats[0]['method'] or "Unknown"
        method_count = method_stats[0]['count']
        method_percentage = round((method_count / total_kills_count) * 100) if total_kills_count > 0 else 0
    
    # Prepare game mode data for the chart
    game_modes_query = """
        SELECT game_mode, COUNT(*) as count
        FROM kills
        WHERE datetime(timestamp) BETWEEN ? AND ?
    """
    game_modes_params = [start_date, end_date]
    
    if selected_game_mode:
        game_modes_query += " AND game_mode = ?"
        game_modes_params.append(selected_game_mode)
        
    game_modes_query += " GROUP BY game_mode ORDER BY count DESC LIMIT 5"
    cursor.execute(game_modes_query, game_modes_params)
    
    # Create explicit lists instead of using .values() method which is causing the error
    game_mode_labels = []
    game_mode_values = []
    
    for row in cursor.fetchall():
        game_mode_name = row['game_mode'] if row['game_mode'] else "Unknown"
        game_mode_labels.append(game_mode_name)
        game_mode_values.append(int(row['count']))
        
    game_modes_data = {
        "labels": game_mode_labels,
        "values": game_mode_values
    }
    
    # Prepare timeline data (kills over time)
    timeline_query = """
        SELECT strftime('%Y-%m-%d', timestamp) as date, COUNT(*) as count
        FROM kills
        WHERE datetime(timestamp) BETWEEN ? AND ?
    """
    timeline_params = [start_date, end_date]
    
    if selected_game_mode:
        timeline_query += " AND game_mode = ?"
        timeline_params.append(selected_game_mode)
        
    timeline_query += " GROUP BY date ORDER BY date ASC LIMIT 30"
    cursor.execute(timeline_query, timeline_params)
    timeline_data = {
        "labels": [],
        "values": []
    }
    
    for row in cursor.fetchall():
        timeline_data["labels"].append(row['date'])
        timeline_data["values"].append(int(row['count']))  # Ensure count is an integer, not a function reference
    
    # Collect player-specific stats
    player_stats = {}
    player_stats_query = """
        SELECT 
            author_id,
            (SELECT game_mode FROM kills k2 
             WHERE k2.author_id = k1.author_id 
             GROUP BY game_mode 
             ORDER BY COUNT(*) DESC LIMIT 1) as favorite_game_mode,
            (SELECT method FROM kills k3 
             WHERE k3.author_id = k1.author_id AND method IS NOT NULL
             GROUP BY method 
             ORDER BY COUNT(*) DESC LIMIT 1) as favorite_method
        FROM kills k1
        WHERE datetime(k1.timestamp) BETWEEN ? AND ?
        GROUP BY author_id
    """
    player_stats_params = [start_date, end_date]
    
    if selected_game_mode:
        player_stats_query = player_stats_query.replace(
            "WHERE datetime(k1.timestamp) BETWEEN ? AND ?",
            "WHERE datetime(k1.timestamp) BETWEEN ? AND ? AND k1.game_mode = ?"
        )
        player_stats_params.append(selected_game_mode)
        
    cursor.execute(player_stats_query, player_stats_params)
    for row in cursor.fetchall():
        player_stats[row['author_id']] = {
            'favorite_game_mode': row['favorite_game_mode'] or 'Unknown',
            'favorite_method': row['favorite_method'] or 'Unknown'
        }
    
    # Continue with the existing leaderboard queries
    base_query = """
        SELECT k.author_id, u.in_game_name, COUNT(*) as total_kills
        FROM kills k
        INNER JOIN user_profiles u ON k.author_id = u.discord_id
        WHERE datetime(k.timestamp) BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    if selected_game_mode:
        base_query += " AND k.game_mode = ?"
        params.append(selected_game_mode)
    base_query += """
        GROUP BY k.author_id, u.in_game_name
        ORDER BY total_kills DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    count_query = """
        SELECT COUNT(DISTINCT k.author_id)
        FROM kills k
        INNER JOIN user_profiles u ON k.author_id = u.discord_id
        WHERE datetime(k.timestamp) BETWEEN ? AND ?
    """
    count_params = [start_date, end_date]
    if selected_game_mode:
        count_query += " AND k.game_mode = ?"
        count_params.append(selected_game_mode)
    cursor.execute(count_query, count_params)
    total_users = cursor.fetchone()[0]
    total_pages = (total_users + per_page - 1) // per_page
    cursor.execute(base_query, params)
    leaderboard_data = cursor.fetchall()
    leaderboard = []
    for row in leaderboard_data:
        author_id = row['author_id']
        in_game_name = row['in_game_name']
        total_kills = row['total_kills']
        cursor.execute("""
            SELECT game_mode, COUNT(*) as mode_count
            FROM kills
            WHERE author_id = ? AND datetime(timestamp) BETWEEN ? AND ?
            GROUP BY game_mode
            ORDER BY mode_count DESC
            LIMIT 1
        """, (author_id, start_date, end_date))
        game_mode_data = cursor.fetchone()
        game_mode_val = game_mode_data[0] if game_mode_data and game_mode_data[0] else 'N/A'
        leaderboard.append({
            'author_id': author_id,
            'in_game_name': in_game_name,
            'total_kills': total_kills,
            'game_mode': game_mode_val
        })
    top_players_query = """
        SELECT k.author_id, u.in_game_name, COUNT(*) as total_kills
        FROM kills k
        INNER JOIN user_profiles u ON k.author_id = u.discord_id
        WHERE datetime(k.timestamp) BETWEEN ? AND ?
    """
    top_players_params = [start_date, end_date]
    if selected_game_mode:
        top_players_query += " AND k.game_mode = ?"
        top_players_params.append(selected_game_mode)
    top_players_query += """
        GROUP BY k.author_id, u.in_game_name
        ORDER BY total_kills DESC
        LIMIT 4
    """
    cursor.execute(top_players_query, top_players_params)
    top_players_data = cursor.fetchall()
    top_players = []
    for row in top_players_data:
        author_id = row['author_id']
        in_game_name = row['in_game_name']
        total_kills = row['total_kills']
        top_kills_query = """
            SELECT player_name, COUNT(*) as kill_count
            FROM kills
            WHERE author_id = ? AND datetime(timestamp) BETWEEN ? AND ?
            GROUP BY player_name
            ORDER BY kill_count DESC
            LIMIT 5
        """
        top_kills_params = [author_id, start_date, end_date]
        cursor.execute(top_kills_query, top_kills_params)
        top_kills = cursor.fetchall()
        top_kills_list = [{
            'player_name': kill[0],
            'kill_count': kill[1]
        } for kill in top_kills]
        top_players.append({
            'author_id': author_id,
            'in_game_name': in_game_name,
            'total_kills': total_kills,
            'top_kills': top_kills_list
        })
    kills_per_user = {}
    for entry in leaderboard:
        user_id_val = entry['author_id']
        kills_query = """
            SELECT id, guild_id, author_id, player_name, victim_engagement, attacker_engagement, timestamp, clip_url, game_mode, player_image
            FROM kills
            WHERE author_id = ? AND datetime(timestamp) BETWEEN ? AND ?
            ORDER BY datetime(timestamp) DESC
        """
        kills_params = [user_id_val, start_date, end_date]
        cursor.execute(kills_query, kills_params)
        kills = cursor.fetchall()
        kills_per_user[user_id_val] = [{
            'id': kill['id'],
            'guild_id': kill['guild_id'],
            'author_id': kill['author_id'],
            'player_name': kill['player_name'],
            'victim_engagement': kill['victim_engagement'],
            'attacker_engagement': kill['attacker_engagement'],
            'timestamp': kill['timestamp'],
            'clip_url': kill['clip_url'],
            'game_mode': kill['game_mode']
        } for kill in kills]
    pagination = {
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'current_page': page,
        'total_pages': total_pages,
        'pages': list(range(1, total_pages + 1))
    }
    return render_template('kill_leaderboard.html',
                        leaderboard=leaderboard,
                        kills_per_user=kills_per_user,
                        total_pages=total_pages,
                        current_page=page,
                        total_kills=total_users,
                        pagination=pagination,
                        guild_id=guild_id,
                        top_players=top_players,
                        game_modes=allowed_game_modes,
                        selected_game_mode=selected_game_mode,
                        patches=list(patch_dates.keys()),
                        selected_patch=selected_patch,
                        is_leaderboard_page=True,
                        # New analytics data
                        total_kills_count=total_kills_count,
                        active_players_count=active_players_count,
                        top_method=top_method,
                        method_percentage=method_percentage,
                        game_modes_data=game_modes_data,
                        timeline_data=timeline_data,
                        player_stats=player_stats)

@api_bp.route('/deaths', methods=['POST'])
@require_api_key
@throttle_requests(max_requests=5000, time_window=60)
@limiter.limit("1000 per minute")
def add_death():
    if g.client_id == 'kill_logger_client':
        is_valid, error_message = is_version_valid(g.client_version)
        if not is_valid:
            logger.warning("Version check failed for user_id: %s, error: %s", g.user_id, error_message)
            return jsonify({'error': error_message}), 426

    try:
        user_id = g.user_id
        guild_id = g.guild_id
        data = request.get_json()
        if not data:
            logger.warning("Invalid JSON data from user_id: %s", user_id)
            return jsonify({'error': 'Invalid JSON data'}), 400

        deaths = []
        skip_count = 0

        # Process data whether it's a list or single record
        if isinstance(data, list):
            for death_data in data:
                death_record = process_death_data(death_data, user_id)
                if not death_record:
                    continue
                deaths.append(death_record)
        else:
            death_record = process_death_data(data, user_id)
            if death_record:
                deaths.append(death_record)

        if not deaths:
            return jsonify({'error': 'No valid death records found'}), 400

        db = get_db()
        cursor = db.cursor()
        previous_changes = db.total_changes

        insert_query = """
            INSERT OR IGNORE INTO death_events (
                id, user_id, guild_id,
                attacker_name, weapon,
                damage_type, timestamp,
                location, game_mode, 
                attacker_ship
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params_list = []
        for record in deaths:
            # Process timestamp similar to kill events
            try:
                raw_ts = record['timestamp']
                if raw_ts.endswith('Z'):
                    raw_ts = raw_ts[:-1] + '+00:00'
                dt = datetime.fromisoformat(raw_ts)
                record_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            except Exception as e:
                logger.warning("Failed to parse timestamp '%s': %s", record['timestamp'], e)
                record_timestamp = record['timestamp']

            # Check for duplicate death events using consistent fields
            duplicate_query = """
                SELECT id FROM death_events
                WHERE user_id = ? 
                  AND attacker_name = ? 
                  AND timestamp = ?
            """
            cursor.execute(duplicate_query, (user_id, record['attacker_name'].lower(), record_timestamp))
            if cursor.fetchone():
                logger.info(
                    "Duplicate death by %s at %s found. Skipping...",
                    record['attacker_name'], record_timestamp
                )
                skip_count += 1
                continue

            params_list.append((
                str(uuid.uuid4()),
                user_id,
                guild_id,
                record['attacker_name'].lower(),
                record.get('weapon', 'Unknown'),
                record.get('damage_type', 'Unknown'),
                record_timestamp,
                record.get('location', 'Unknown'),
                record.get('game_mode', 'Unknown'),
                record.get('attacker_ship', 'Unknown')
            ))

        # Only execute if we have parameters to insert
        if params_list:
            cursor.executemany(insert_query, params_list)
            
            # Use the retry mechanism for database commit
            def commit_operation():
                db.commit()
                return db.total_changes - previous_changes
                
            inserted_count = retry_on_db_lock(commit_operation)
        else:
            inserted_count = 0

        if inserted_count == 0:
            if skip_count > 0:
                logger.info("All deaths were duplicates; returning 201 to avoid client retry loops.")
                return jsonify({'message': "All deaths were duplicates; nothing logged."}), 201
            else:
                logger.warning("No death records were inserted and none were duplicates.")
                return jsonify({'message': "No valid death records to insert."}), 200

        # Notify via socket.io
        for record in deaths:
            notification_payload = {
                "guild_id": guild_id,
                "user_id": user_id,
                "attacker_name": record['attacker_name'],
                "weapon": record.get('weapon', 'Unknown'),
                "damage_type": record.get('damage_type', 'Unknown'),
                "timestamp": record['timestamp'],
                "game_mode": record.get('game_mode', 'Unknown'),
                "location": record.get('location', 'Unknown'),
                "attacker_ship": record.get('attacker_ship', 'Unknown')
            }
            try:
                socketio.emit("new_death", notification_payload)
                redis_client.publish("death_notifications", json.dumps(notification_payload))
            except Exception as e:
                logger.error("Failed to publish death notification: %s", e)

        return jsonify({
            'message': f'{inserted_count} death record(s) added successfully. Duplicates skipped: {skip_count}'
        }), 201

    except Exception as e:
        logger.exception("An error occurred in add_death route: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/kills/update-clip', methods=['POST'])
@require_api_key
def update_kill_clip():
    """Update a kill record with a Twitch clip URL"""
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if not data:
            logger.warning(f"Invalid JSON data from user_id: {user_id}")
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Log the incoming data for debugging
        logger.debug(f"Received clip update data: {data}")
        
        clip_url = data.get('clip_url')
        if not clip_url:
            logger.warning(f"Missing clip URL from user_id: {user_id}")
            return jsonify({'error': 'Missing clip URL'}), 400
        
        # We'll use several methods to find the correct kill to update
        kill_id = data.get('kill_id')
        timestamp = data.get('timestamp')
        victim_name = data.get('victim_name')
        
        db = get_db()
        cursor = db.cursor()
        
        if kill_id:
            # Update by kill ID if provided
            cursor.execute("""
                UPDATE kills
                SET clip_url = ?
                WHERE id = ? AND author_id = ?
            """, (clip_url, kill_id, user_id))
        
        elif timestamp:
            # If we have a timestamp, try to find the most recent kill at that time
            logger.info(f"Looking for kill with timestamp near {timestamp}")
            
            # Parse the timestamp to handle different formats
            try:
                # Replace trailing 'Z' with '+00:00' for fromisoformat compatibility
                if timestamp.endswith('Z'):
                    timestamp = timestamp[:-1] + '+00:00'
                dt = datetime.fromisoformat(timestamp)
                # Format timestamp for SQLite query
                formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.warning(f"Failed to parse timestamp '{timestamp}': {e}")
                formatted_timestamp = timestamp
                
            # Find the kill within a small time window (30 seconds before and after)
            # This should handle the case when the exact victim name is unknown
            query = """
                SELECT id FROM kills
                WHERE author_id = ?
                  AND datetime(timestamp) BETWEEN datetime(?, '-30 seconds') AND datetime(?, '+30 seconds')
                ORDER BY datetime(timestamp) DESC
                LIMIT 1
            """
            params = [user_id, formatted_timestamp, formatted_timestamp]
            
            # If we have a victim name, add it to the query for better precision
            if victim_name:
                query = """
                    SELECT id FROM kills
                    WHERE author_id = ?
                      AND LOWER(player_name) = ?
                      AND datetime(timestamp) BETWEEN datetime(?, '-10 seconds') AND datetime(?, '+10 seconds')
                    ORDER BY datetime(timestamp) DESC
                    LIMIT 1
                """
                params = [user_id, victim_name.lower(), formatted_timestamp, formatted_timestamp]
            
            cursor.execute(query, params)
            kill = cursor.fetchone()
            
            if kill:
                kill_id = kill[0]
                cursor.execute("""
                    UPDATE kills
                    SET clip_url = ?
                    WHERE id = ?
                """, (clip_url, kill_id))
                logger.info(f"Found kill with ID {kill_id} by timestamp {timestamp}")
            else:
                logger.warning(f"No matching kill found for timestamp {timestamp}")
                return jsonify({'error': 'No matching kill found'}), 404
        else:
            logger.warning("Not enough information to identify the kill record")
            return jsonify({'error': 'Not enough information to identify the kill record'}), 400
        
        # Use the retry mechanism for database commit
        def commit_operation():
            db.commit()
            return cursor.rowcount
            
        updated_count = retry_on_db_lock(commit_operation)
        
        if updated_count > 0:
            logger.info(f"Updated clip URL for kill {kill_id}, user {user_id}")
            
            # Send notification about the clip update
            try:
                cursor.execute("""
                    SELECT guild_id, author_id, player_name, timestamp, game_mode
                    FROM kills
                    WHERE id = ?
                """, (kill_id,))
                kill_data = cursor.fetchone()
                
                if kill_data:
                    notification_payload = {
                        "guild_id": kill_data['guild_id'] if isinstance(kill_data, dict) else kill_data[0],
                        "author_id": kill_data['author_id'] if isinstance(kill_data, dict) else kill_data[1],
                        "player_name": kill_data['player_name'] if isinstance(kill_data, dict) else kill_data[2],
                        "timestamp": kill_data['timestamp'] if isinstance(kill_data, dict) else kill_data[3],
                        "clip_url": clip_url,
                        "kill_id": kill_id,
                        "game_mode": kill_data['game_mode'] if isinstance(kill_data, dict) else kill_data[4]
                    }
                    socketio.emit("clip_added", notification_payload)
                    redis_client.publish("clip_notifications", json.dumps(notification_payload))
            except Exception as e:
                logger.error(f"Failed to publish clip notification: {e}")
            
            return jsonify({'message': 'Clip URL updated successfully', 'kill_id': kill_id}), 200
        else:
            logger.warning(f"No kill updated with clip URL for user {user_id}")
            return jsonify({'error': 'No kill updated'}), 404
            
    except Exception as e:
        logger.exception(f"Error updating clip URL: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@web_bp.route('/personal_deaths')
def personal_deaths():
    if 'user_id' not in session:
        flash("Please log in to view your personal deaths.", "warning")
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    guild_id = session.get('guild_id')
    
    if not guild_id:
        flash("No guild selected.", "error")
        return redirect(url_for('pick_server'))
        
    patch_dates = PATCH_DATES
    patch = request.args.get('patch', 'ALL')
    
    if patch != 'ALL' and patch not in patch_dates:
        flash("Invalid patch specified.", "error")
        return redirect(url_for('pick_server'))
        
    if patch == 'ALL':
        start_date = "1950-01-01 00:00:00"
        end_date = "2030-01-01 00:00:00"
    else:
        start_date, end_date = patch_dates[patch]
        
    search_query = request.args.get('search_query', '').strip()
    game_mode = request.args.get('game_mode', None)
    
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
        
    per_page = 50
    offset = (page - 1) * per_page
    
    db = get_db()
    cursor = db.cursor()
    
    query_conditions = ["d.user_id = ?", "datetime(d.timestamp) BETWEEN ? AND ?"]
    params = [user_id, start_date, end_date]
    
    if search_query:
        query_conditions.append("LOWER(d.attacker_name) LIKE ?")
        params.append(f"%{search_query.lower()}%")
        
    if game_mode:
        query_conditions.append("d.game_mode = ?")
        params.append(game_mode)
        
    where_clause = " AND ".join(query_conditions)
    
    base_query = f"""
        SELECT 
            d.id, d.attacker_name, d.weapon, 
            d.damage_type, d.timestamp, d.location,
            d.game_mode, d.attacker_ship,
            p.enlistment_date, p.occupation, p.org_name, p.org_tag
        FROM death_events d
        LEFT JOIN player_info p ON LOWER(d.attacker_name) = LOWER(p.player_name)
        WHERE {where_clause}
        ORDER BY datetime(d.timestamp) DESC
        LIMIT ? OFFSET ?
    """
    
    params_extended = params + [per_page, offset]
    
    count_query = f"SELECT COUNT(*) as count FROM death_events d WHERE {where_clause}"
    cursor.execute(count_query, params)
    total_deaths = cursor.fetchone()['count']
    
    total_pages = (total_deaths + per_page - 1) // per_page
    
    if page < 1:
        page = 1
    elif page > total_pages:
        page = max(total_pages, 1)
        
    cursor.execute(base_query, params_extended)
    rows = cursor.fetchall()
    
    deaths_list = []
    for row in rows:
        deaths_list.append({
            'id': row['id'],
            'attacker_name': row['attacker_name'],
            'weapon': row['weapon'],
            'damage_type': row['damage_type'],
            'timestamp': row['timestamp'],
            'location': row['location'],
            'game_mode': row['game_mode'],
            'attacker_ship': row['attacker_ship'],
            'enlistment_date': row['enlistment_date'],
            'occupation': row['occupation'],
            'org_name': row['org_name'],
            'org_tag': row['org_tag']
        })
    
    # Get statistics
    weapon_counts = {}
    attacker_counts = {}
    ship_counts = {}
    
    stats_query = f"""
        SELECT weapon, attacker_name, attacker_ship, COUNT(*) as count
        FROM death_events
        WHERE {where_clause}
        GROUP BY weapon, attacker_name, attacker_ship
    """
    
    cursor.execute(stats_query, params)
    stats_rows = cursor.fetchall()
    
    for row in stats_rows:
        weapon = row['weapon'] or 'Unknown'
        attacker = row['attacker_name'] or 'Unknown'
        ship = row['attacker_ship'] or 'Unknown'
        count = row['count']
        
        weapon_counts[weapon] = weapon_counts.get(weapon, 0) + count
        attacker_counts[attacker] = attacker_counts.get(attacker, 0) + count
        ship_counts[ship] = ship_counts.get(ship, 0) + count
    
    most_deadly_weapon = max(weapon_counts.items(), key=lambda x: x[1])[0] if weapon_counts else "N/A"
    top_killer = max(attacker_counts.items(), key=lambda x: x[1])[0] if attacker_counts else "N/A"
    most_deadly_ship = max(ship_counts.items(), key=lambda x: x[1])[0] if ship_counts else "N/A"
    
    pagination = {
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'current_page': page,
        'total_pages': total_pages,
        'pages': list(range(1, total_pages + 1))
    }
    
    return render_template(
        'personal_deaths.html',
        deaths=deaths_list,
        total_pages=total_pages,
        current_page=page,
        total_deaths=total_deaths,
        search_query=search_query,
        patch=patch,
        game_mode=game_mode,
        patches=list(patch_dates.keys()),
        game_modes=[
            "Team Elimination", "PU", "Gun Rush", "Tonk Royale", "Free Flight",
            "Squadron Battle", "Vehicle Kill Confirmed", "FPS Kill Confirmed",
            "Control", "Duel"
        ],
        guild_id=guild_id,
        most_deadly_weapon=most_deadly_weapon,
        top_killer=top_killer,
        most_deadly_ship=most_deadly_ship
    )

def retry_on_db_lock(operation, max_retries=5, retry_delay=0.2):
    """
    Retry a database operation when encountering a database lock.
    
    Args:
        operation: A callable that performs the database operation
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (increases exponentially)
        
    Returns:
        Result of the operation if successful
        
    Raises:
        Original exception if max_retries exceeded
    """
    retries = 0
    while True:
        try:
            return operation()
        except sqlite3.OperationalError as e:
            if "database is locked" not in str(e) or retries >= max_retries:
                logger.error(f"Database operation failed after {retries} retries: {e}")
                raise
            
            retries += 1
            sleep_time = retry_delay * (2 ** (retries - 1))  # Exponential backoff
            logger.warning(f"Database locked, retrying operation in {sleep_time:.2f}s (attempt {retries}/{max_retries})")
            time.sleep(sleep_time)

def get_version_from_file():
    """Read the latest version from the JSON file."""
    file_path = os.path.join(os.path.dirname(__file__), 'latest_version.json')
    with open(file_path, 'r') as f:
        version_data = json.load(f)
        return version_data['latest_version']