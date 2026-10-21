def run_job(job):
    try:
        job.execute()
    except ValueError:
        pass

def run_job_logged(job):
    try:
        job.execute()
    except ValueError:
        job.mark_failed()
