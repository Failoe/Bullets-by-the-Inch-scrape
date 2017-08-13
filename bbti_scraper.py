import requests
import sqlite3
from bs4 import BeautifulSoup as bs
import re

console_output = True


def create_db_tables():
	"""
	This creates our SQLite database and adds the only table
	we are using to it.  The "IF EXISTS" and "IF NOT EXISTS"
	are there to reset the database whenever we rerun the code.
	"""
	bbti_conn = sqlite3.connect('bbti.db')
	bbti_cur = bbti_conn.cursor()
	bbti_cur.execute("""DROP TABLE IF EXISTS fps""")
	bbti_cur.execute("""CREATE TABLE IF NOT EXISTS fps (test_type text,
														caliber text,
														weapon_name text,
														barrel_length,
														cartridge text,
														fps int,
														bullet_weight_grains int)
														""")
	bbti_conn.commit()
	bbti_conn.close()


def fetch_caliber_data(url):
	caliber_page = requests.get("http://www.ballisticsbytheinch.com/{0}".format(url))
	caliber_soup = bs(caliber_page.content, 'html5lib')

	""" Finds both tables on the page and builds the column header list """
	for table in caliber_soup.find_all('tbody'):
		header = table.tr.extract()
		first_column = header.td.extract()

		""" Set the value for the first item in the columns list """
		if 'barrel length' in first_column:
			columns = ['barrel length (inches)']
		else:
			columns = ['real world weapon']

		for column in header.find_all('td'):
			for column_header in column.find_all('a'):
				for breaker in column_header.find_all('br'):  # Replaces <br/> tags with a space
					column_header.br.replace_with(' ')
				columns.append(column_header.text)  # Adds cartridge name to columns list

		# Opens database connection
		bbti_conn = sqlite3.connect('bbti.db')
		bbti_cur = bbti_conn.cursor()

		"""
		The following loop parses through both tables
		on each page and adds them to the sqlite database
		"""
		for row in table.find_all('tr'):
			for item in range(len(columns)):
				row_data = row.find_all('td')[item]
				if item == 0:
					if row_data.find('font'):
						""" Checks if the first row is from the barrel length table or
							real world weapon table and handles the headers """
						bbl_length = row_data.font.extract().text.replace('" barrel', '')  # Barrel length
						for breaker in row_data.find_all('br'):
							row_data.br.replace_with(' ')
						rww_name = row_data.text.strip()  # Parses and sets real world weapon name
					else:
						bbl_length = row_data.text.replace('"', '')
						rww_name = None
					gr = None
				else:  # Parses the bullet's weight in grains from the header
					grains = columns[item]
					gr = re.search(r'(\d+) gr.', grains).group(1)
				if item != 0:
					if console_output:
						print(columns[0], url.replace('.html', ''), rww_name, bbl_length, columns[item], row_data.text.strip(), gr)
					bbti_cur.execute("""INSERT INTO fps (	test_type,
															caliber,
															weapon_name,
															barrel_length,
															cartridge,
															fps,
															bullet_weight_grains)
											VALUES (?, ?, ?, ?, ?, ?, ?)""",
											(
												columns[0],
												url.replace('.html', ''),
												rww_name,
												bbl_length,
												columns[item],
												row_data.text.strip(),
												gr
												)
											)

		# Commits data to the database and closes the connection
		bbti_conn.commit()
		bbti_conn.close()


def main():
	calibers_page = requests.get('http://www.ballisticsbytheinch.com/calibers.html')
	calibers_soup = bs(calibers_page.content, 'html5lib')
	caliber_links = []
	for li in calibers_soup.find_all('li'):
		if "http://www" not in li.a.get('href'):
			caliber_links.append(li.a.get('href'))

	create_db_tables()
	[fetch_caliber_data(x) for x in caliber_links]


if __name__ == '__main__':
	main()
