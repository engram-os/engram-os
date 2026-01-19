GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'


printf "${CYAN}INITIALIZING LOCAL AI OPERATING SYSTEM...${NC}\n"


printf "%s\n" "---------------------------------------"
printf "${GREEN}Starting Docker Infrastructure (Brain, Worker, Clock)...${NC}\n"
docker-compose up -d


printf "%s\n" "---------------------------------------"
printf "${GREEN}Waiting for API to come online...${NC}"

until curl -s -f -o /dev/null "http://localhost:8000/docs"; do
    printf "."
    sleep 2
done
printf " ${GREEN}Online!${NC}\n"


printf "%s\n" "---------------------------------------"
printf "Starting Browser Watcher...\n"
nohup python3 browser_sync.py > browser.log 2>&1 &
PID_BROWSER=$!
echo $PID_BROWSER > .browser_pid
printf "Browser Watcher running (PID: $PID_BROWSER)\n"

printf "%s\n" "---------------------------------------"
printf "Starting File Ingestor...\n"
nohup python3 ingestor.py > ingestor.log 2>&1 &
PID_INGEST=$!
echo $PID_INGEST > .ingestor_pid
printf "Ingestor running (PID: $PID_INGEST)\n"


printf "%s\n" "---------------------------------------"
printf "Starting Streamlit Dashboard...\n"
nohup python3 -m streamlit run app.py > streamlit.log 2>&1 &
PID_UI=$!
echo $PID_UI > .streamlit_pid
printf "Dashboard running (PID: $PID_UI)\n"


printf "%s\n" "---------------------------------------"
printf "${CYAN}SYSTEM ONLINE${NC}\n"
printf "   - API:        http://localhost:8000\n"
printf "   - Dashboard:  http://localhost:8501\n"
printf "   - Agent:      Autonomous (Runs every 15 mins)\n"
printf "   - Ingestor:   Watching 'data/inbox' folder\n"
printf "\n"
printf "To shut down, run: ./stop_os.sh\n"
printf "%s\n" "---------------------------------------"