module.exports = {
    ci: {
        collect: {
            url: [
                'http://localhost:8000/',
                'http://localhost:8000/members/',
                'http://localhost:8000/members/hemingway/',
                'http://localhost:8000/members/hemingway/borrowing/',
                'http://localhost:8000/members/hemingway/membership/',
                'http://localhost:8000/members/hemingway/cards/',
                'http://localhost:8000/members/hemingway/cards/9af2d811-6084-4967-a4d7-5c0481658011/',
                'http://localhost:8000/books/',
                'http://localhost:8000/books/dial/',
                'http://localhost:8000/books/dial/circulation/',
                'http://localhost:8000/books/dial/cards/',
                'http://localhost:8000/analysis/',
                'http://localhost:8000/analysis/2019/11/test-analysis/',
                'http://localhost:8000/sources/',
                'http://localhost:8000/sources/cards/',
                'http://localhost:8000/about/',
                'http://localhost:8000/about/technical/'
            ],
            startServerCommand: 'python manage.py runserver --insecure',
            startServerReadyPattern: 'Quit the server with CONTROL-C.'
        },
        upload: {
            target: 'temporary-public-storage',
        },
    },
};