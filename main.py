from apis.stock_market import get_stock_details


def main():
    print("Hello from smartfolio!")


if __name__ == "__main__":
    result = get_stock_details.invoke({"stock_name": "Reliance"})
    #print(result)
