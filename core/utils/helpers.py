# Funções auxiliares
def get_total(cursor, query):
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else 0