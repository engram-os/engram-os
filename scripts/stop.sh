echo "SHUTTING DOWN AI OS..."

echo "---------------------------------------"
echo "Stopping Docker Containers..."
docker-compose stop

echo "---------------------------------------"
if [ -f .ingestor_pid ]; then
    PID=$(cat .ingestor_pid)
    echo "Killing Ingestor (PID: $PID)..."
    kill $PID 2>/dev/null
    rm .ingestor_pid
fi

if [ -f .streamlit_pid ]; then
    PID=$(cat .streamlit_pid)
    echo "Killing Dashboard (PID: $PID)..."
    kill $PID 2>/dev/null
    rm .streamlit_pid
fi

if [ -f .browser_pid ]; then
    PID=$(cat .browser_pid)
    echo "Killing Browser Watcher (PID: $PID)..."
    kill $PID 2>/dev/null
    rm .browser_pid
fi

echo "System Offline. Have a nice day."