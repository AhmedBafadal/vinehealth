# Vine Health Test

App using Docker, docker-compose & Flask.

# How to Run
```
docker-compose up --build
```

# How it works
Please access app in steps listed below using Postman or similar:
1. /user endpoint - pass in name & password for account
2. /login - enter same login details to get jwt token
3. /licence - using jwt in header ('x-access-token')
4. /licences - using jwt in header ('x-access-token')