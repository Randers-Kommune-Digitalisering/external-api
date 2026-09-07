FROM python:3.13-alpine

# Set dir and user
ENV GROUP_NAME=app
ENV HOME=/app
ENV GROUP_ID=11000
ENV USER_ID=11001
ENV PORT=8080

# Add user
RUN addgroup --gid $GROUP_ID $GROUP_NAME && \
    adduser $USER_ID -u $USER_ID -D -G $GROUP_NAME -h $HOME

# Install packages
RUN apk update
RUN apk add --no-cache build-base postgresql-dev freetds-dev

# Copy files and set working dir
COPY . $HOME
WORKDIR $HOME

# Set permissions
RUN chown -R $USER_ID:$GROUP_ID $HOME && chmod -R 775 $HOME

# Install python packages
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Open port
EXPOSE $PORT

# Set user
USER $USER_ID

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} main:app"]