import { test as base, expect, type Page } from '@playwright/test'
import { login } from './helpers'

// Test user credentials
export const TEST_USER = {
  username: 'testuser_e2e',
  email: 'testuser_e2e@example.com',
  password: 'TestPassword123!',
}

// Extended test fixture with logged-in page
export type TestFixtures = {
  /** Page with authenticated user session */
  loggedInPage: Page
  /** Test user credentials */
  testUser: typeof TEST_USER
}

/**
 * Extended test with custom fixtures
 * @example
 * import { test } from './fixtures'
 *
 * test('access protected page', async ({ loggedInPage }) => {
 *   await loggedInPage.goto('/dashboard')
 * })
 */
export const test = base.extend<TestFixtures>({
  // Test user fixture
  testUser: async ({}, use) => {
    await use(TEST_USER)
  },

  // Logged-in page fixture - creates a new page with active session
  loggedInPage: async ({ browser, testUser }, use) => {
    // Create a new context and page
    const context = await browser.newContext()
    const page = await context.newPage()

    // Perform login
    await login(page, testUser.username, testUser.password)

    // Use the authenticated page
    await use(page)

    // Cleanup
    await context.close()
  },
})

export { expect }
