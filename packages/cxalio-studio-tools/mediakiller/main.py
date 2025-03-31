import click


@click.group()
def main():
    pass

@main.command()
def hello():
    click.echo('Hello, World!')

@main.command()
def bye():
    click.echo('Goodbye, World!')

if __name__ == '__main__':
    main()