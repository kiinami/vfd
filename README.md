<div align="center">

<h1>
  ✈️ 👁️

VFD
</h1>

</div>

VFD is a small service that tracks the price of flights on Google Flights, stores the historical data, allows you to
view it in a simple web interface, and sends notifications when there is a new best price.

The project uses the really nice [fast-flights](https://github.com/AWeirdDev/flights) library to scrape the data from
Google Flights, the [Streamlit](https://streamlit.io/) library to create the web interface,
and [apprise](https://github.com/caronc/apprise) to send notifications.

This project is still in its early stages, so there are a lot of features that I would like to add in the future. If you have any suggestions, feel free to open an issue or a pull request.

## Features

- Continuous scraping of flight prices from Google Flights (currently only in dollars)
- Possibility to set a range of dates and cities to depart and arrive from
- Storing of historical data by hour
- Simple web interface to view the data
- Notifications when a new best price is found

## Docker installation

Installing the project with Docker is the easiest way to get started. You will need to have Docker and Docker Compose
installed on your system.

1. Get the `docker-compose.yml` file
   from [here](https://raw.githubusercontent.com/kiinami/vfd/refs/heads/main/docker-compose.yml)
2. Get the `.env` file from [here](https://raw.githubusercontent.com/kiinami/vfd/refs/heads/main/.env.example) and fill
   in the necessary information
3. Run `docker compose up -d` to start VFD
4. Open `http://localhost:4242` in your browser to view the web interface (although you won't see much until a few
   hours' worth of data has been collected)

## Local installation

1. This project uses [uv](https://docs.astral.sh/uv/) to manage the virtual environment, so you will need to install it first. Refer to the documentation on how to install it on your system.
2. Clone the repository
3. Copy the `.env.example` file to `.env` and fill in the necessary information
4. Run `uv sync` to install the dependencies and set up the project
5. To run the scrapper, run `uv run scrapper`. You can also run `uv run scrapper --help` to see the available options,
   including the possibility to run the scrapper once instead of continuously.
6. To run the web interface, run `uv run dashboard`

## Configuration

The configuration is done through the `.env` file. Here is a list of the available options:

| Variable                          | Description                                                                                                                                                                  | Default   | Required |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|----------|
| `VFD_DATABASE`                    | The path to the SQLite database file                                                                                                                                         | -         | Yes      |
| `VFD_SCRAPPER_START_DATES`        | The possible dates to start the trip                                                                                                                                         | -         | Yes      |
| `VFD_SCRAPPER_END_DATES`          | The possible dates to end the trip                                                                                                                                           | -         | Yes      |
| `VFD_SCRAPPER_END_DATES`          | The possible dates to end the trip                                                                                                                                           | -         | Yes      |
| `VFD_SCRAPPER_DEPARTURE_AIRPORTS` | The possible source airports                                                                                                                                                 | -         | Yes      |
| `VFD_SCRAPPER_ARRIVAL_AIRPORTS`   | The possible destination airports                                                                                                                                            | -         | Yes      |
| `VFD_SCRAPPER_INTERVAL`           | The interval in seconds between each query                                                                                                                                   | `60`      | No       |
| `VFD_SCRAPPER_NOTIFICATION_URLS`  | Apprise notification URLs (comma separated) (for more info, check [the Apprise documentation](https://github.com/caronc/apprise?tab=readme-ov-file#supported-notifications)) | -         | Yes      |
| `VFD_SCRAPPER_VERBOSE`            | Whether to print debug information for the scrapper                                                                                                                          | `False`   | No       |
| `VFD_DASHBOARD_HOST`              | The host to run the dashboard on                                                                                                                                             | `0.0.0.0` | No       |
| `VFD_DASHBOARD_PORT`              | The port to run the dashboard on                                                                                                                                             | `4242`    | No       |

## To-do

- [x] Dockerize the project with a cron job to run the scrapper regularly
  - [x] Job scheduling
  - [x] `Dockerfile` and `docker-compose.yml`
  - [x] Handling of `.env` file
  - [x] `.dockerignore`
  - [x] Image building and publishing with GitHub Actions
- [x] Add a small web interface to view the data
- [x] Add a way to send notifications when the price of a flight drops below the last best price
- [x] Stage queries in batches to avoid problems with Google
- [ ] Configurable resolution of the data (currently only by hour)
- [ ] Add support for proxies to avoid being blocked by Google
- [ ] Add authentication support with [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator)
- [ ] More granularity in start and end ranges
- [ ] Add support to track different trips at the same time

## FAQ

### Why this thing?

I want to go on a trip with my friends to a faraway land, the dates are more or less set, we could arrive and depart
from a set of cities, and I want to get the cheapest flight combination possible.

I could do this manually, but it would take a great deal of time and effort (96 different combinations to check every
day), so I decided to automate it.

### What does VFD stand for?

Verifiable Flight Data, of course. What else could VFD stand for?

## Contributing

If you have any suggestions, feel free to open an issue or a pull request. The local installation instructions should
suffice to get you started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.txt) file for details.
