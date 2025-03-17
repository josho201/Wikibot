def area_parallelogram(vertices):
    x1, y1 = vertices[0]
    x2, y2 = vertices[1]
    x3, y3 = vertices[2]
    x4, y4 = vertices[3]

    # Calculamos los vectores de dos lados adyacentes
    side1 = (x2 - x1, y2 - y1)
    side2 = (x3 - x1, y3 - y1)

    # Usamos la formula del producto vectorial para calcular el area
    area = abs(side1[0]*side2[1] - side1[1]*side2[0]) / 2.0
    return area