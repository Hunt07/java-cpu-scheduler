package com.cpuscheduler.model;

public class Process {
    private int pid;
    private int arrivalTime;
    private int burstTime;
    private int remainingTime;
    private int priority;
    private int waitingTime;
    private int turnaroundTime;
    private int completionTime;
    private int responseTime;
    private String state;

    public Process(int pid, int arrivalTime, int burstTime, int priority) {
        this.pid = pid;
        this.arrivalTime = arrivalTime;
        this.burstTime = burstTime;
        this.remainingTime = burstTime;
        this.priority = priority;
        this.waitingTime = 0;
        this.turnaroundTime = 0;
        this.completionTime = 0;
        this.responseTime = -1;
        this.state = "ready";
    }

    // Getters
    public int getPid() { return pid; }
    public int getArrivalTime() { return arrivalTime; }
    public int getBurstTime() { return burstTime; }
    public int getRemainingTime() { return remainingTime; }
    public int getPriority() { return priority; }
    public int getWaitingTime() { return waitingTime; }
    public int getTurnaroundTime() { return turnaroundTime; }
    public int getCompletionTime() { return completionTime; }
    public int getResponseTime() { return responseTime; }
    public String getState() { return state; }

    // Setters
    public void setRemainingTime(int remainingTime) { this.remainingTime = remainingTime; }
    public void setWaitingTime(int waitingTime) { this.waitingTime = waitingTime; }
    public void setTurnaroundTime(int turnaroundTime) { this.turnaroundTime = turnaroundTime; }
    public void setCompletionTime(int completionTime) { this.completionTime = completionTime; }
    public void setResponseTime(int responseTime) { this.responseTime = responseTime; }
    public void setState(String state) { this.state = state; }

    public void updateState(String newState, int currentTime) {
        if (!this.state.equals(newState)) {
            this.state = newState;
            if (newState.equals("running")) {
                if (responseTime == -1) {
                    responseTime = currentTime - arrivalTime;
                }
            } else if (newState.equals("completed")) {
                completionTime = currentTime;
                turnaroundTime = completionTime - arrivalTime;
                waitingTime = turnaroundTime - burstTime;
            }
        }
    }

    private boolean isValid() {
        return arrivalTime >= 0 && burstTime > 0 && priority >= 0;
    }

    @Override
    public String toString() {
        return String.format("P%d [Arrival=%d, Burst=%d, Priority=%d, State=%s]",
            pid, arrivalTime, burstTime, priority, state);
    }
}