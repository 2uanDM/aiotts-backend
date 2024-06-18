# Run the server in tmux
uvicorn app.main:app --reload --host 0.0.0.0 --port 1234


# Authorization
sudo chown -R $USER:$USER /home/