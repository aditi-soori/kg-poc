from utils import process_data

def main():
    data = get_data()
    result = process_data(data)
    print(result)

def get_data():
    return [1, 2, 3]

if __name__ == "__main__":
    main()