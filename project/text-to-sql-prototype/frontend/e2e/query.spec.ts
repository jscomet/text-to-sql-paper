import { test, expect } from './fixtures'

test.describe('Query Flow', () => {
  test('should complete full query workflow', async ({ authPage }) => {
    // Navigate to query page
    await authPage.goto('/query')

    // Verify query page is loaded
    await expect(authPage.locator('h2')).toContainText('自然语言查询')

    // Select database connection
    await authPage.click('[data-testid="connection-select"]')
    await authPage.click('.el-select-dropdown__item:has-text("Test Connection")')

    // Enter natural language question
    await authPage.fill('[data-testid="question-input"]', '查询所有用户')

    // Click generate SQL button
    await authPage.click('[data-testid="generate-sql-button"]')

    // Wait for SQL generation
    await expect(authPage.locator('[data-testid="sql-editor"]')).toBeVisible()
    await expect(authPage.locator('[data-testid="sql-editor"]')).toContainText('SELECT')

    // Execute SQL
    await authPage.click('[data-testid="execute-sql-button"]')

    // Wait for results
    await expect(authPage.locator('[data-testid="query-results"]')).toBeVisible()
  })

  test('should show error for invalid question', async ({ authPage }) => {
    await authPage.goto('/query')

    // Try to generate without selecting connection
    await authPage.fill('[data-testid="question-input"]', 'test question')
    await authPage.click('[data-testid="generate-sql-button"]')

    // Should show error
    await expect(authPage.locator('.el-message--error')).toBeVisible()
  })

  test('should toggle SQL editor visibility', async ({ authPage }) => {
    await authPage.goto('/query')

    // Check SQL editor is visible by default
    await expect(authPage.locator('[data-testid="sql-editor"]')).toBeVisible()

    // Toggle off
    await authPage.click('[data-testid="toggle-sql-editor"]')
    await expect(authPage.locator('[data-testid="sql-editor"]')).not.toBeVisible()

    // Toggle on
    await authPage.click('[data-testid="toggle-sql-editor"]')
    await expect(authPage.locator('[data-testid="sql-editor"]')).toBeVisible()
  })

  test('should save query to history', async ({ authPage }) => {
    await authPage.goto('/query')

    // Perform a query
    await authPage.fill('[data-testid="question-input"]', '查询订单数量')
    await authPage.click('[data-testid="generate-sql-button"]')

    // Wait for generation
    await authPage.waitForTimeout(2000)

    // Navigate to history
    await authPage.goto('/history')

    // Verify query appears in history
    await expect(authPage.locator('text=查询订单数量')).toBeVisible()
  })
})
