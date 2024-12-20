def cart_stats(cart):
    total_quantity, total_amount = 0, 0
    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['price']
    return {'total_quantity': total_quantity, 'total_price': total_amount}