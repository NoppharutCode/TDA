def quicksort(A, lo, hi):
    if lo < hi:
        p = partition(A, lo, hi)
        quicksort(A, lo, p-1)
        quicksort(A, p + 1, hi)

def partition(A, lo,hi):
    temp = 0
    pivot = A[hi]
    i = lo -1
    for j in range(lo, hi) :
        if A[j] >= pivot :
            i = i +1
            temp = A[i]
            A[i] = A[j]
            A[j] = temp
    temp = A[i+1]
    A[i+1] = A[hi]
    A[hi] = temp
    return i+1


A = [15, 9,23,1,46,32,12,6,41,86]

quicksort(A, 0, 9)
print(A)