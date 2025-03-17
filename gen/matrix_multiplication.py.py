```python
import numpy as np

def multiply_matrices(matrix_a, matrix_b):
    # Get the dimensions of the input matrices
    rows_a = len(matrix_a)
    cols_a = len(matrix_a[0])
    rows_b = len(matrix_b)
    cols_b = len(matrix_b[0])

    # Check if the matrices can be multiplied
    if cols_a != rows_b:
        raise ValueError("Number of columns in matrix A must equal number of rows in matrix B")

    # Initialize the result matrix with zeros
    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]

    # Perform matrix multiplication using nested loops
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):  # or rows_b, since cols_a == rows_b
                result[i][j] += matrix_a[i][k] * matrix_b[k][j]

    return result

# Example matrices (you can replace these with your own input)
matrix_a = np.array([[1, 2], [3, 4]])
matrix_b = np.array([[5, 6], [7, 8]])

result = multiply_matrices(matrix_a.tolist(), matrix_b.tolist())
print("Result of matrix multiplication:")
for row in result:
    print(row)
```