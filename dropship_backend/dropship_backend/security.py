"""Security utilities for input sanitization and injection prevention."""

import re
import html
from html import escape
from typing import Any, Dict, List, Optional, Union


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize a string by removing dangerous characters and limiting length."""
    if not isinstance(value, str):
        return str(value)
    
    sanitized = value.strip()
    sanitized = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', sanitized)
    
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_html(value: str) -> str:
    """Sanitize HTML content to prevent XSS."""
    if not isinstance(value, str):
        return str(value)
    
    return escape(value)


def sanitize_email(email: str) -> str:
    """Sanitize and validate email address."""
    if not isinstance(email, str):
        return ''
    
    email = email.strip().lower()
    email = re.sub(r'[^\w.@+-]', '', email)
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return ''
    
    return email[:254]


def sanitize_phone(phone: str) -> str:
    """Sanitize phone number to only allow digits, +, -, (, )."""
    if not isinstance(phone, str):
        return ''
    
    return re.sub(r'[^\d\+\-\(\)\s]', '', phone)[:20]


def sanitize_integer(value: Any, default: int = 0, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """Sanitize and validate integer input."""
    try:
        result = int(value)
    except (ValueError, TypeError):
        return default
    
    if min_val is not None and result < min_val:
        result = min_val
    if max_val is not None and result > max_val:
        result = max_val
    
    return result


def sanitize_uuid(value: Any) -> Optional[str]:
    """Validate and sanitize UUID input."""
    if not isinstance(value, str):
        return None
    
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    value = value.lower().strip()
    
    if re.match(uuid_pattern, value):
        return value
    
    return None


def sanitize_list(value: Any, max_items: int = 100) -> List:
    """Sanitize list input."""
    if not isinstance(value, list):
        return []
    
    return value[:max_items]


def sanitize_dict(value: Any, allowed_keys: Optional[List[str]] = None) -> Dict:
    """Sanitize dictionary input."""
    if not isinstance(value, dict):
        return {}
    
    if allowed_keys:
        return {k: v for k, v in value.items() if k in allowed_keys}
    
    return dict(value)


def sanitize_search_query(query: str, max_length: int = 200) -> str:
    """Sanitize search query to prevent injection."""
    if not isinstance(query, str):
        return ''
    
    query = query.strip()
    query = re.sub(r'[<>\"\'%;()&+]', '', query)
    query = re.sub(r'\s+', ' ', query)
    
    return query[:max_length]


def strip_html_tags(html_string: str) -> str:
    """Strip all HTML tags from a string."""
    if not isinstance(html_string, str):
        return str(html_string)
    
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_string)


def validate_and_sanitize_input(data: Dict, schema: Dict) -> tuple[Dict, List[str]]:
    """
    Validate and sanitize input data based on a schema.
    
    Schema format:
    {
        'field_name': {
            'type': 'string|integer|email|phone|uuid|list|dict',
            'required': bool,
            'max_length': int,
            'min_value': int,
            'max_value': int,
            'allowed_keys': list (for dict type)
        }
    }
    """
    result = {}
    errors = []
    
    for field_name, rules in schema.items():
        value = data.get(field_name)
        
        if rules.get('required') and (value is None or value == ''):
            errors.append(f"Field '{field_name}' is required")
            continue
        
        if value is None or value == '':
            continue
        
        field_type = rules.get('type', 'string')
        
        try:
            if field_type == 'string':
                result[field_name] = sanitize_string(value, rules.get('max_length', 500))
            elif field_type == 'email':
                result[field_name] = sanitize_email(value)
            elif field_type == 'phone':
                result[field_name] = sanitize_phone(value)
            elif field_type == 'integer':
                result[field_name] = sanitize_integer(
                    value, 
                    min_val=rules.get('min_value'),
                    max_val=rules.get('max_value')
                )
            elif field_type == 'uuid':
                result[field_name] = sanitize_uuid(value)
            elif field_type == 'list':
                result[field_name] = sanitize_list(value, rules.get('max_items', 100))
            elif field_type == 'dict':
                result[field_name] = sanitize_dict(value, rules.get('allowed_keys'))
            else:
                result[field_name] = str(value)
        except Exception:
            errors.append(f"Invalid value for field '{field_name}'")
    
    return result, errors


def sanitize_user_input(data: Dict) -> Dict:
    """Sanitize all user input data."""
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, int):
            sanitized[key] = sanitize_integer(value)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        else:
            sanitized[key] = value
    
    return sanitized