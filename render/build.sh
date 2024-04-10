# Exit on error
ser -o errexit

# Modify this line as needed for your package manager
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

python manage.py tailwind build