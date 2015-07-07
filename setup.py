import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-slack',
    version='0.1',
    packages=['slack'],
    include_package_data=True,
    license='MIT License',
    description='Django Slack',
    long_description=README,
    url='https://github.com/prontodev/django-slack',
    author='R&D Pronto Marketing',
    author_email='rd@prontomarketing.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
