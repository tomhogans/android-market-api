sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install git python-pip -y
git clone git://github.com/tomhsx/android-market-api.git ~/apk-downloader
sudo pip install -r ~/apk-downloader/requirements.txt
