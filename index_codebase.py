# WALK THROUGH ALL FOLDERS AND IDENTIFY EACH .py FILE
import sys
import os

def main():
   
    arguments = (sys.argv[1:])
    directory = arguments[0]

    for root,dirs,files in os.walk(directory):
      for file in files:
            if file.endswith(".py"):
                print(os.path.join(root, file))
main()