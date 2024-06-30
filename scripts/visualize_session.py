from src.visualizer import visualize_episode
import click
import os


@click.command()
@click.option('-d', '--directory', required=True, help='Absolute path to the session directory')
def main(directory):
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and file.endswith('.h5'):
            visualize_episode(file_path)


if __name__ == '__main__':
    main()