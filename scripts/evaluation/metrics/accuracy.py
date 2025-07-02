# accuracy.py
def accuracy(results):
    if not results:
        return 0.0
    return sum(results) / len(results)
