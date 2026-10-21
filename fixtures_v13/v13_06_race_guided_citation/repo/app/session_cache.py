class SessionCache:
    async def refresh(self):
        self.token = await fetch_token()
