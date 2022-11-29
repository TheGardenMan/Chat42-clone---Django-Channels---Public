sudo apt install python3-pip -y

sudo apt install python-is-python3 -y


# install postgres before requirements.txt

sudo apt install postgresql postgresql-contrib -y

sudo -i -u postgres

psql -->
	"ALTER USER postgres WITH ENCRYPTED PASSWORD'pwd_here'";

/etc/postgresql/12/main/pg_hba.conf ==> change first 2 peer to md5 
# or just use the pg installation script (with hardcoded pwd and del the script afterwards)

create the tables via psql from `tables_for_prod.sql`

sudo apt install libpq-dev #req for psycopg2

git clone https://github.com/TheGardenMan/C42.git

sudo pip install -r requirements_ubuntu.txt
daphne failed when ran under
install redis - https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-20-04  (Install and change the "supervised systemd".. skip other steps)

python manage.py migrate
python manage.py makemigrations

copy daphne.service and match.service to /etc/systemd/system/
systemctl daemon-reload
systemctl start daphne && systemctl status daphne
systemctl daemon-reload && systemctl stop match && systemctl start match && systemctl status match