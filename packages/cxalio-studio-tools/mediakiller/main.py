from mediakiller.application import Application


def main():
    with Application() as app:
        app.run()


if __name__ == "__main__":
    main()
