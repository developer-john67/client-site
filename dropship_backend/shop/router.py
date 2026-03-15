class CassandraRouter:
    """
    Routes Cassandra models to the cassandra database,
    and everything else (auth, sessions, etc.) to default (SQLite).
    """

    # ← Added 'products', 'users', 'cart', 'orders' so all
    #   custom Cassandra models route correctly
    cassandra_apps = {'shop', 'products', 'users', 'cart', 'orders'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.cassandra_apps:
            return 'cassandra'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.cassandra_apps:
            return 'cassandra'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.cassandra_apps:
            return db == 'cassandra'
        return db == 'default'