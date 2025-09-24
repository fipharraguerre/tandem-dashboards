from db import get_db
import datetime

def update_client_status():
    db = get_db()
    cursor = db.cursor()

    # Obtener todos los clientes
    cursor.execute("SELECT nombre FROM clientes")
    clients = cursor.fetchall()

    for client in clients:
        client_name = client[0]

        # Obtener todos los hostnames asociados a este cliente
        cursor.execute("SELECT host_name FROM client_hosts WHERE client_name = %s", (client_name,))
        hostnames = cursor.fetchall()

        # Inicializar las variables para contadores de Backup Jobs
        success_count_backup = 0
        warn_count_backup = 0
        fail_count_backup = 0

        # Inicializar las variables para contadores de Tiering Jobs
        success_count_tiering = 0
        warn_count_tiering = 0
        fail_count_tiering = 0

        # Inicializar las variables para contadores de Replication Jobs
        success_count_replication = 0
        warn_count_replication = 0
        fail_count_replication = 0

        # Variable to store the latest datetime value
        last_seen = None

        # Inicializar mensaje para "VeeamConfigurationBackup"
        config_backup_status = None

        # Recorrer cada hostname y consultar sus resultados
        for host in hostnames:
            host_name = host[0]

            # Acumular para BackupJob y Backup
            cursor.execute(f"""
                SELECT
                    SUM(CASE WHEN result IN ('Success', 'ok', 'Completed') AND type LIKE '%Backup%' THEN 1 ELSE 0 END) AS success_count_backup,
                    SUM(CASE WHEN result = 'Warn' AND type LIKE '%Backup%' THEN 1 ELSE 0 END) AS warn_count_backup,
                    SUM(CASE WHEN result = 'Fail' AND type LIKE '%Backup%' THEN 1 ELSE 0 END) AS fail_count_backup,
                    MAX(CASE WHEN type LIKE '%Backup%' THEN datetime ELSE NULL END) AS last_seen_backup  -- Get the latest datetime for this host
                FROM `{host_name}`
            """)
            result_backup = cursor.fetchone()
            success_count_backup += result_backup[0]
            warn_count_backup += result_backup[1]
            fail_count_backup += result_backup[2]

            # Update last_seen if last_seen_backup is more recent
            if result_backup[3]:  # and (last_seen is None or result_backup[3] > last_seen):
                last_seen = result_backup[3]

            # Acumular para TieringJob
            cursor.execute(f"""
                SELECT
                    SUM(CASE WHEN result IN ('Success', 'ok', 'Completed') AND type = 'TieringJob' THEN 1 ELSE 0 END) AS success_count_tiering,
                    SUM(CASE WHEN result = 'Warn' AND type = 'TieringJob' THEN 1 ELSE 0 END) AS warn_count_tiering,
                    SUM(CASE WHEN result = 'Fail' AND type = 'TieringJob' THEN 1 ELSE 0 END) AS fail_count_tiering,
                    MAX(CASE WHEN type = 'TieringJob' THEN datetime ELSE NULL END) AS last_seen_tiering
                FROM `{host_name}`
            """)
            result_tiering = cursor.fetchone()
            success_count_tiering += result_tiering[0]
            warn_count_tiering += result_tiering[1]
            fail_count_tiering += result_tiering[2]

            # Update last_seen if last_seen_tiering is more recent
            if result_tiering[3]:  # and (last_seen is None or result_tiering[3] > last_seen):
                last_seen = result_tiering[3]

            # Acumular para Replication Jobs (looking for 'Repl' in vmname)
            cursor.execute(f"""
                SELECT
                    SUM(CASE WHEN result IN ('Success', 'ok', 'Completed') AND vmname LIKE '%Repl%' THEN 1 ELSE 0 END) AS success_count_replication,
                    SUM(CASE WHEN result = 'Warn' AND vmname LIKE '%Repl%' THEN 1 ELSE 0 END) AS warn_count_replication,
                    SUM(CASE WHEN result = 'Fail' AND vmname LIKE '%Repl%' THEN 1 ELSE 0 END) AS fail_count_replication,
                    MAX(CASE WHEN vmname LIKE '%Repl%' THEN datetime ELSE NULL END) AS last_seen_replication
                FROM `{host_name}`
            """)
            result_replication = cursor.fetchone()
            success_count_replication += result_replication[0]
            warn_count_replication += result_replication[1]
            fail_count_replication += result_replication[2]

            # Update last_seen if last_seen_replication is more recent
            if result_replication[3]:  # and (last_seen is None or result_replication[3] > last_seen):
                last_seen = result_replication[3]

            # Obtener estado de VeeamConfigurationBackup
            cursor.execute(f"""
                SELECT result
                FROM `{host_name}`
                WHERE type = 'VeeamConfigurationBackup'
                ORDER BY datetime DESC
                LIMIT 1
            """)
            result_config_backup = cursor.fetchone()
            if result_config_backup:
                config_backup_status = result_config_backup[0]  # Guardar el último estado encontrado

        # Actualizar el estado del cliente basado en los resultados para BackupJob y Backup
        if fail_count_backup > 0:
            estado = 'fail'
            statusMsg1 = f'{fail_count_backup} job(s) failed in the last 24 hours'
        elif warn_count_backup > 0:
            estado = 'warn'
            statusMsg1 = f'{warn_count_backup} Warning(s) in the last 24 hours'
        else:
            estado = 'ok'
            statusMsg1 = f'{success_count_backup} jobs were successful in the last 24 hours'

        # Configurar el mensaje para TieringJob
        if fail_count_tiering > 0:
            statusMsg2 = f'{fail_count_tiering} offload(s) failed in the last 24 hours'
            # si los backups concluyeron bien pero fallaron los offloads, marcar estado warn
            if estado == 'ok':
                estado = 'warn'
        elif warn_count_tiering > 0:
            statusMsg2 = f'{warn_count_tiering} warning(s) in the last 24 hours'
        elif success_count_tiering > 0:
            statusMsg2 = f'{success_count_tiering} offload(s) were successful in the last 24 hours'
        else:
            statusMsg2 = 'N/A'

        # Configurar el mensaje para Replication Jobs
        if fail_count_replication > 0:
            statusMsg4 = f'{fail_count_replication} replication(s) failed in the last 24 hours'
            # si los backups concluyeron bien pero fallaron las replicaciones, marcar estado warn
            if estado == 'ok':
                estado = 'warn'
        elif warn_count_replication > 0:
            statusMsg4 = f'{warn_count_replication} replication warning(s) in the last 24 hours'
            # si los backups concluyeron bien pero hay warnings en replicaciones, marcar estado warn
            if estado == 'ok':
                estado = 'warn'
        elif success_count_replication > 0:
            statusMsg4 = f'{success_count_replication} replication(s) were successful in the last 24 hours'
        else:
            statusMsg4 = 'N/A'

        # Guardar el mensaje y el estado en la tabla clientes
        cursor.execute("""
            UPDATE clientes 
            SET estado = %s, msgA = %s, msgB = %s, msgC = %s, msgD = %s, last_seen = %s
            WHERE nombre = %s
        """, (estado, statusMsg1, statusMsg2, config_backup_status, statusMsg4, last_seen, client_name))

        db.commit()
