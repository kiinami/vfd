# VFD

VFD (Verifiable Flight Data) is a small script that tracks the price of flights on Google Flights and (for now) saves the data to an SQLite database so you can use it however you see fit.

The project uses the really nice [fast-flights](https://github.com/AWeirdDev/flights) library to scrape the data from Google Flights. 

This project is still in its early stages, so there are a lot of features that I would like to add in the future. If you have any suggestions, feel free to open an issue or a pull request.

## Installation

1. This project uses [uv](https://docs.astral.sh/uv/) to manage the virtual environment, so you will need to install it first. Refer to the documentation on how to install it on your system.
2. Clone the repository
3. Copy the `.env.example` file to `.env` and fill in the necessary information
4. Run the scrapper in Docker with `docker compose up -d`
5. Alternatively, you can run the scrapper locally once with `uv run scrapper -r`. Run `uv run scrapper --help` to see all the available options.

## To-do

- [ ] Dockerize the project with a cron job to run the scrapper regularly
  - [x] Job scheduling
  - [x] `Dockerfile` and `docker-compose.yml`
  - [x] Handling of `.env` file
  - [x] `.dockerignore`
  - [ ] Image building and publishing with GitHub Actions
- [ ] Stage queries in batches to avoid problems with Google
- [ ] Add a small web interface to view the data
- [ ] Add a way to send notifications when the price of a flight drops below a certain threshold
