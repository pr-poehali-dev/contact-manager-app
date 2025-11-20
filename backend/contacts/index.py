'''
Business: Управление контактами (поиск, отправка/принятие заявок, список контактов)
Args: event с httpMethod, body, queryStringParameters, headers; context с request_id
Returns: HTTP response со списком контактов или статусом операции
'''

import json
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ValidationError

import psycopg2

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)

class ContactRequest(BaseModel):
    contact_email: str = Field(..., min_length=1)

class RequestAction(BaseModel):
    request_id: int
    action: str = Field(..., pattern='^(accept|reject)$')

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def get_user_from_token(token: str) -> Optional[int]:
    return 1

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    headers = event.get('headers', {})
    user_token = headers.get('X-User-Token') or headers.get('x-user-token')
    
    if not user_token:
        return {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Требуется авторизация'}),
            'isBase64Encoded': False
        }
    
    user_id = get_user_from_token(user_token)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        if method == 'GET':
            params = event.get('queryStringParameters', {})
            action = params.get('action', 'list')
            
            if action == 'list':
                cur.execute("""
                    SELECT u.id, u.email, u.name, u.avatar_url, c.created_at
                    FROM contacts c
                    JOIN users u ON c.contact_user_id = u.id
                    WHERE c.user_id = %s AND c.status = 'accepted'
                    ORDER BY c.created_at DESC
                """, (user_id,))
                
                contacts = []
                for row in cur.fetchall():
                    contacts.append({
                        'id': row[0],
                        'email': row[1],
                        'name': row[2],
                        'avatar_url': row[3],
                        'added_at': row[4].isoformat() if row[4] else None
                    })
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'contacts': contacts}),
                    'isBase64Encoded': False
                }
            
            elif action == 'requests':
                cur.execute("""
                    SELECT c.id, u.id, u.email, u.name, u.avatar_url, c.created_at
                    FROM contacts c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.contact_user_id = %s AND c.status = 'pending'
                    ORDER BY c.created_at DESC
                """, (user_id,))
                
                requests = []
                for row in cur.fetchall():
                    requests.append({
                        'request_id': row[0],
                        'user_id': row[1],
                        'email': row[2],
                        'name': row[3],
                        'avatar_url': row[4],
                        'created_at': row[5].isoformat() if row[5] else None
                    })
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'requests': requests}),
                    'isBase64Encoded': False
                }
            
            elif action == 'sent':
                cur.execute("""
                    SELECT c.id, u.id, u.email, u.name, u.avatar_url, c.status, c.created_at
                    FROM contacts c
                    JOIN users u ON c.contact_user_id = u.id
                    WHERE c.user_id = %s AND c.status = 'pending'
                    ORDER BY c.created_at DESC
                """, (user_id,))
                
                sent = []
                for row in cur.fetchall():
                    sent.append({
                        'request_id': row[0],
                        'user_id': row[1],
                        'email': row[2],
                        'name': row[3],
                        'avatar_url': row[4],
                        'status': row[5],
                        'created_at': row[6].isoformat() if row[6] else None
                    })
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'sent_requests': sent}),
                    'isBase64Encoded': False
                }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            action = body_data.get('action')
            
            if action == 'search':
                req = SearchRequest(**body_data)
                
                cur.execute("""
                    SELECT id, email, name, avatar_url
                    FROM users
                    WHERE (name ILIKE %s OR email ILIKE %s) AND id != %s
                    LIMIT 20
                """, (f'%{req.query}%', f'%{req.query}%', user_id))
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'id': row[0],
                        'email': row[1],
                        'name': row[2],
                        'avatar_url': row[3]
                    })
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'results': results}),
                    'isBase64Encoded': False
                }
            
            elif action == 'send_request':
                req = ContactRequest(**body_data)
                
                cur.execute("SELECT id FROM users WHERE email = %s", (req.contact_email,))
                contact = cur.fetchone()
                
                if not contact:
                    return {
                        'statusCode': 404,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Пользователь не найден'}),
                        'isBase64Encoded': False
                    }
                
                contact_user_id = contact[0]
                
                cur.execute("""
                    SELECT id FROM contacts 
                    WHERE user_id = %s AND contact_user_id = %s
                """, (user_id, contact_user_id))
                
                if cur.fetchone():
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Заявка уже отправлена'}),
                        'isBase64Encoded': False
                    }
                
                cur.execute("""
                    INSERT INTO contacts (user_id, contact_user_id, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id
                """, (user_id, contact_user_id))
                
                conn.commit()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True, 'message': 'Заявка отправлена'}),
                    'isBase64Encoded': False
                }
            
            elif action == 'handle_request':
                req = RequestAction(**body_data)
                
                cur.execute("""
                    SELECT user_id FROM contacts 
                    WHERE id = %s AND contact_user_id = %s AND status = 'pending'
                """, (req.request_id, user_id))
                
                if not cur.fetchone():
                    return {
                        'statusCode': 404,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Заявка не найдена'}),
                        'isBase64Encoded': False
                    }
                
                new_status = 'accepted' if req.action == 'accept' else 'rejected'
                cur.execute("""
                    UPDATE contacts SET status = %s WHERE id = %s
                """, (new_status, req.request_id))
                
                conn.commit()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True, 'message': 'Заявка обработана'}),
                    'isBase64Encoded': False
                }
        
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Неверное действие'}),
            'isBase64Encoded': False
        }
    
    finally:
        cur.close()
        conn.close()
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }
