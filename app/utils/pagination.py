import math
from typing import List, Any

def get_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    limit: int
) -> dict:
    """Формирует ответ с пагинацией в нужном формате"""
    total_pages = math.ceil(total / limit) if total > 0 else 0
    
    return {
        "data": items,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages
        }
    }