# Exit on error
ser -o errexit

pip install -r requirements.txt

pip manage.py collectstatic --no-input

pip manage.py migrate

pip manage.py tailwind build