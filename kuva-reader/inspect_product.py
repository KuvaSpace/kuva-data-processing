import argparse
from pathlib import Path
from kuva_reader import Level1Product

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process a Level 1 product path.')
    # The path is a folder that should contain a .tiff file and a .json file with the metadata
    parser.add_argument('product_path', type=str, help='The path to the L1 product')

    # Parse the arguments
    args = parser.parse_args()

    # Convert the provided path to a Path object
    product_path = Path(args.product_path)

    # Initialize and use the Level1Product
    product = Level1Product(product_path)
    
    print(f"Product image shape: {product.image.shape}")
    
if __name__ == '__main__':
    main()