from fabric.api import env, execute
from fabric.operations import run, put

env.roledefs= {'downloaders': [
    'ubuntu@ec2-54-235-67-142.compute-1.amazonaws.com',
    'ubuntu@ec2-54-235-67-162.compute-1.amazonaws.com',
    'ubuntu@ec2-54-235-81-208.compute-1.amazonaws.com',
    'ubuntu@ec2-54-235-81-212.compute-1.amazonaws.com',
    'ubuntu@ec2-54-242-145-19.compute-1.amazonaws.com',

    'ubuntu@ec2-50-16-144-159.compute-1.amazonaws.com',
    'ubuntu@ec2-72-44-63-4.compute-1.amazonaws.com',
    'ubuntu@ec2-23-22-16-53.compute-1.amazonaws.com',
    'ubuntu@ec2-54-224-4-230.compute-1.amazonaws.com',
    'ubuntu@ec2-184-72-77-246.compute-1.amazonaws.com',

    'ubuntu@ec2-184-73-25-166.compute-1.amazonaws.com',
    'ubuntu@ec2-23-20-97-185.compute-1.amazonaws.com',
    'ubuntu@ec2-107-21-140-131.compute-1.amazonaws.com',
    'ubuntu@ec2-50-19-157-3.compute-1.amazonaws.com',
    'ubuntu@ec2-204-236-202-93.compute-1.amazonaws.com',
]}

env.roles = ['downloaders']


def stalled():
    run("ps aux | grep \"python\"")

def logs():
    run("tail ~/apk-downloader/downloader.log")

def clearlogs():
    run("rm ~/apk-downloader/downloader.log")

def update():
    run("cd ~/apk-downloader/; git pull")
    put("newconfig.json", "~/apk-downloader/")

