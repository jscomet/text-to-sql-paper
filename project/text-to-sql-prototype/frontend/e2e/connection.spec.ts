import { test, expect } from './fixtures'

test.describe('Connection Management', () => {
  test('should create new database connection', async ({ authPage }) => {
    await authPage.goto('/connections')

    // Click add connection button
    await authPage.click('[data-testid="add-connection-button"]')

    // Fill connection form
    await authPage.fill('[data-testid="connection-name"]', 'Test SQLite DB')
    await authPage.selectOption('[data-testid="db-type"]', 'sqlite')
    await authPage.fill('[data-testid="database-path"]', ':memory:')

    // Save connection
    await authPage.click('[data-testid="save-connection"]')

    // Verify success message
    await expect(authPage.locator('.el-message--success')).toBeVisible()

    // Verify connection appears in list
    await expect(authPage.locator('text=Test SQLite DB')).toBeVisible()
  })

  test('should test connection before saving', async ({ authPage }) => {
    await authPage.goto('/connections')
    await authPage.click('[data-testid="add-connection-button"]')

    // Fill form
    await authPage.fill('[data-testid="connection-name"]', 'Test Connection')
    await authPage.selectOption('[data-testid="db-type"]', 'sqlite')
    await authPage.fill('[data-testid="database-path"]', ':memory:')

    // Test connection
    await authPage.click('[data-testid="test-connection"]')

    // Wait for test result
    await expect(authPage.locator('.el-message')).toBeVisible()
  })

  test('should delete connection', async ({ authPage }) => {
    await authPage.goto('/connections')

    // Create a connection first
    await authPage.click('[data-testid="add-connection-button"]')
    await authPage.fill('[data-testid="connection-name"]', 'To Delete')
    await authPage.selectOption('[data-testid="db-type"]', 'sqlite')
    await authPage.fill('[data-testid="database-path"]', ':memory:')
    await authPage.click('[data-testid="save-connection"]')

    // Delete the connection
    await authPage.click('[data-testid="delete-connection-To Delete"]')

    // Confirm deletion
    await authPage.click('.el-button:has-text("确认")')

    // Verify connection removed
    await expect(authPage.locator('text=To Delete')).not.toBeVisible()
  })

  test('should view connection schemas', async ({ authPage }) => {
    await authPage.goto('/connections')

    // Click on a connection to view schemas
    await authPage.click('[data-testid="view-schemas-connection-1"]')

    // Verify schema view opens
    await expect(authPage.locator('[data-testid="schema-tree"]')).toBeVisible()
  })
})
