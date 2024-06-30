from src.visualizer import visualize_episode
import click


@click.command()
@click.option('-f', '--file_path', required=False, help='Absolute path to the episode file.')
def main(file_path):
    visualize_episode(file_path)

if __name__ == '__main__':
    main()