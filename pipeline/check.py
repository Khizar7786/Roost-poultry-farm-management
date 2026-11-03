"""Report the available device without requiring a GPU."""
import torch


def main():
    if torch.cuda.is_available():
        print(f"CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA unavailable; use device: cpu (the default).")


if __name__ == "__main__":
    main()
