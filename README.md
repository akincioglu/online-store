# Online Store

This is an online store application where users can view products, add them to their cart, and place orders.

## Features

- View products
- Search and filter products
- Add products to the cart
- View and edit the cart
- Place orders
- Create user accounts and log in
- Manage user profiles


## Run Locally

Clone project

```bash
  $ git clone git@github.com:akincioglu/online-store.git
```

Go to the project directory

```bash
  $ cd online-store
```

Create a virtual environment

```bash
  $ python -m virtualenv virtualenv-name
```

Activate the virtual environment

```bash
  $ source venv/Scripts/activate (Windows)
  $ source venv/bin/activate (macOS/Linux)
```

Install required packages

```bash
  $ pip install -r requirements.txt
```

Create a superuser

```bash
  $ python manage.py createsuperuser
```

Run project

```bash
  $ python manage.py runserver
```

# Environment Variables
To run this project, you will need to add the following environment variables to your **.env** file *(You can see an example of it in the .env.example file located in the main directory of the project.)*:

```bash
DATABASES_DEFAULT_ENGINE=django.db.backends.postgresql
DATABASES_DEFAULT_NAME=your-db-name
DATABASES_DEFAULT_USER=your-db-username
DATABASES_DEFAULT_PASSWORD=your-db-password
DATABASES_DEFAULT_HOST=localhost
DATABASES_DEFAULT_PORT=5432
```
