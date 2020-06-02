module.exports = {
    ci: {
        collect: {
            url: ['http://localhost:8000/'],
            startServerCommand: 'python manage.py runserver --insecure'
        },
        upload: {
            target: 'temporary-public-storage',
        },
    },
};