import os
import requests
from jira import JIRA
from pydantic import BaseModel
from typing import List, Optional

# --- Standardized Task Model ---
class Task(BaseModel):
    id: str
    title: str
    status: str
    priority: str
    source: str 
    url: str

class IntegrationManager:
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_token = os.getenv("JIRA_TOKEN")
        self.jira_email = os.getenv("JIRA_EMAIL")
        
        self.linear_key = os.getenv("LINEAR_KEY")

    def get_jira_tasks(self) -> List[Task]:
        if not self.jira_token:
            return []
        
        try:
            # Connect to Jira
            jira = JIRA(server=self.jira_url, basic_auth=(self.jira_email, self.jira_token))
            
            # Query: Assigned to me AND not done
            jql = 'assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC'
            issues = jira.search_issues(jql, maxResults=10)
            
            tasks = []
            for issue in issues:
                tasks.append(Task(
                    id=issue.key,
                    title=issue.fields.summary,
                    status=issue.fields.status.name,
                    priority=issue.fields.priority.name if hasattr(issue.fields, 'priority') else "Medium",
                    source="Jira",
                    url=f"{self.jira_url}/browse/{issue.key}"
                ))
            return tasks
        except Exception as e:
            print(f" Jira Error: {e}")
            return []

    def get_linear_tasks(self) -> List[Task]:
        if not self.linear_key:
            return []

        url = "https://api.linear.app/graphql"
        headers = {"Authorization": self.linear_key, "Content-Type": "application/json"}
        
        # GraphQL Query for "My Active Issues"
        query = """
        query {
          viewer {
            assignedIssues(filter: { state: { type: { neq: "completed" } } }) {
              nodes {
                identifier
                title
                priorityLabel
                state { name }
                url
              }
            }
          }
        }
        """
        
        try:
            response = requests.post(url, headers=headers, json={"query": query}, timeout=(5, 10))
            if response.status_code != 200:
                return []
                
            data = response.json()
            nodes = data.get("data", {}).get("viewer", {}).get("assignedIssues", {}).get("nodes", [])
            
            tasks = []
            for node in nodes:
                tasks.append(Task(
                    id=node['identifier'],
                    title=node['title'],
                    status=node['state']['name'],
                    priority=node['priorityLabel'] or "No Priority",
                    source="Linear",
                    url=node['url']
                ))
            return tasks
        except Exception as e:
            print(f" Linear Error: {e}")
            return []

    def get_combined_briefing_data(self):
        """Fetch everything and sort by priority"""
        jira = self.get_jira_tasks()
        linear = self.get_linear_tasks()
        all_tasks = jira + linear
        return all_tasks