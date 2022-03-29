import imp
import os

from flask import Flask


def create_app(test_config=None): 
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev', 
        DATABASE=os.path.join(app.instance_path, 'archive.db'), 
        DL_CONF_PATH=os.path.join(app.root_path, 'config.yaml')
    )

    if test_config is None: 
        # load instance config if exists
        app.config.from_pyfile('config.py', silent=True)
    else: 
        app.config.from_mapping(test_config)

    # create instance folder
    try: 
        os.makedirs(app.instance_path)
    except OSError: 
        pass

    from vtbarchiver import (api, channels, db_functions, download_functions,
                             home, management, videos)

    app.teardown_appcontext(db_functions.close_db)
    app.cli.add_command(db_functions.init_db_command)
    app.cli.add_command(management.add_admin_command)
    app.cli.add_command(download_functions.download_channels_command)
    app.cli.add_command(management.regenerate_search_index)
    
    app.register_blueprint(management.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(channels.bp)
    app.register_blueprint(videos.bp)
    app.register_blueprint(api.bp)

    return app
