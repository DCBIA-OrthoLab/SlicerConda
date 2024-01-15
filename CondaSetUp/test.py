import sys

def salutation(args):
    print('je suis le grand mechant loup')
    print(args["mot1"])
    print(args["mot2"])
    print(args["mot3"])

if __name__ == "__main__":
    

    print("Starting")
    print(sys.argv)


    args = {
        "mot1": sys.argv[1],
        "mot2": sys.argv[2],
        "mot3": sys.argv[3]
        
    }
    # args = {}
    
    salutation(args)