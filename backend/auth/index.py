'''
Business: Авторизация и регистрация пользователей (email/пароль и Google)
Args: event с httpMethod, body, queryStringParameters; context с request_id
Returns: HTTP response с токеном или ошибкой
'''

import json
import os
import hashlib
import secrets
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field, ValidationError

# Подключение к БД
import psycopg2

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    google_id: str = Field(..., min_length=1)
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method == 'POST':
        body_data = json.loads(event.get('body', '{}'))
        action = body_data.get('action')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            if action == 'register':
                req = RegisterRequest(**body_data)
                password_hash = hash_password(req.password)
                
                cur.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (req.email,)
                )
                if cur.fetchone():
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Email уже зарегистрирован'}),
                        'isBase64Encoded': False
                    }
                
                cur.execute(
                    "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s) RETURNING id, email, name, avatar_url",
                    (req.email, req.name, password_hash)
                )
                user = cur.fetchone()
                conn.commit()
                
                token = generate_token()
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'token': token,
                        'user': {
                            'id': user[0],
                            'email': user[1],
                            'name': user[2],
                            'avatar_url': user[3]
                        }
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'login':
                req = LoginRequest(**body_data)
                password_hash = hash_password(req.password)
                
                cur.execute(
                    "SELECT id, email, name, avatar_url FROM users WHERE email = %s AND password_hash = %s",
                    (req.email, password_hash)
                )
                user = cur.fetchone()
                
                if not user:
                    return {
                        'statusCode': 401,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({'error': 'Неверный email или пароль'}),
                        'isBase64Encoded': False
                    }
                
                token = generate_token()
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'token': token,
                        'user': {
                            'id': user[0],
                            'email': user[1],
                            'name': user[2],
                            'avatar_url': user[3]
                        }
                    }),
                    'isBase64Encoded': False
                }
            
            elif action == 'google':
                req = GoogleAuthRequest(**body_data)
                
                cur.execute(
                    "SELECT id, email, name, avatar_url FROM users WHERE google_id = %s",
                    (req.google_id,)
                )
                user = cur.fetchone()
                
                if user:
                    token = generate_token()
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({
                            'token': token,
                            'user': {
                                'id': user[0],
                                'email': user[1],
                                'name': user[2],
                                'avatar_url': user[3]
                            }
                        }),
                        'isBase64Encoded': False
                    }
                else:
                    cur.execute(
                        "INSERT INTO users (email, name, google_id, avatar_url) VALUES (%s, %s, %s, %s) RETURNING id, email, name, avatar_url",
                        (req.email, req.name, req.google_id, req.avatar_url)
                    )
                    user = cur.fetchone()
                    conn.commit()
                    
                    token = generate_token()
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                        'body': json.dumps({
                            'token': token,
                            'user': {
                                'id': user[0],
                                'email': user[1],
                                'name': user[2],
                                'avatar_url': user[3]
                            }
                        }),
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
