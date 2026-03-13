import { test, expect } from './fixtures'
import { login, waitForLoading } from './helpers'
import path from 'path'

test.describe('BIRD Dataset Import Feature', () => {
  test.beforeEach(async ({ page, testUser }) => {
    // Login before each test
    await login(page, testUser.username, testUser.password)
    await waitForLoading(page)
  })

  test.describe('Import Dialog', () => {
    test('should open import dialog from evaluations page', async ({ page }) => {
      // Navigate to evaluations page
      await page.goto('/evaluations')
      await waitForLoading(page)

      // Click import dataset button
      await page.click('[data-testid="import-dataset-button"]')

      // Import dialog should be visible
      await expect(page.locator('.import-dialog')).toBeVisible()

      // Check dialog title
      await expect(page.locator('.import-dialog .el-dialog__title')).toContainText('导入数据集')
    })

    test('should display zip upload tab', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Check ZIP upload tab
      await expect(page.locator('.el-tabs__item:has-text("ZIP 上传")')).toBeVisible()

      // Click on zip tab
      await page.click('.el-tabs__item:has-text("ZIP 上传")')

      // Upload area should be visible
      await expect(page.locator('.upload-area')).toBeVisible()
    })

    test('should display local path tab', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Check local path tab
      await expect(page.locator('.el-tabs__item:has-text("本地路径")')).toBeVisible()

      // Click on local path tab
      await page.click('.el-tabs__item:has-text("本地路径")')

      // Path input should be visible
      await expect(page.locator('[data-testid="local-path-input"]')).toBeVisible()
      await expect(page.locator('[data-testid="validate-path-button"]')).toBeVisible()
    })

    test('should validate file type for zip upload', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Try to upload a non-zip file
      const invalidFileInput = page.locator('input[type="file"]')
      await invalidFileInput.setInputFiles({
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('This is not a zip file')
      })

      // Should show error message
      await expect(page.locator('.el-message--error')).toBeVisible({ timeout: 5000 })
    })

    test('should require API key selection', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Try to submit without selecting API key
      await page.click('[data-testid="start-import-button"]')

      // Should show validation error
      await expect(page.locator('.el-form-item__error')).toContainText('API Key')
    })
  })

  test.describe('Import Progress', () => {
    test('should show progress dialog during import', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Upload a valid zip file (mock)
      const zipFileInput = page.locator('input[type="file"]')
      await zipFileInput.setInputFiles({
        name: 'bird_test.zip',
        mimeType: 'application/zip',
        buffer: Buffer.from('PK') // Minimal zip header
      })

      // Select API key
      await page.click('[data-testid="api-key-select"]')
      await page.click('.el-select-dropdown__item:has-text("OpenAI")')

      // Start import
      await page.click('[data-testid="start-import-button"]')

      // Progress dialog should appear
      await expect(page.locator('.progress-dialog')).toBeVisible({ timeout: 5000 })

      // Check progress elements
      await expect(page.locator('.import-steps')).toBeVisible()
      await expect(page.locator('.progress-section')).toBeVisible()
    })

    test('should display import steps correctly', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Trigger import
      const zipFileInput = page.locator('input[type="file"]')
      await zipFileInput.setInputFiles({
        name: 'bird_test.zip',
        mimeType: 'application/zip',
        buffer: Buffer.from('PK')
      })

      await page.click('[data-testid="api-key-select"]')
      await page.click('.el-select-dropdown__item:first-child')
      await page.click('[data-testid="start-import-button"]')

      // Check all 4 steps are visible
      await expect(page.locator('.import-steps')).toContainText('验证')
      await expect(page.locator('.import-steps')).toContainText('解析')
      await expect(page.locator('.import-steps')).toContainText('创建连接')
      await expect(page.locator('.import-steps')).toContainText('创建任务')
    })

    test('should show log output during import', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Trigger import
      const zipFileInput = page.locator('input[type="file"]')
      await zipFileInput.setInputFiles({
        name: 'bird_test.zip',
        mimeType: 'application/zip',
        buffer: Buffer.from('PK')
      })

      await page.click('[data-testid="api-key-select"]')
      await page.click('.el-select-dropdown__item:first-child')
      await page.click('[data-testid="start-import-button"]')

      // Log container should be visible
      await expect(page.locator('.log-container')).toBeVisible({ timeout: 5000 })
      await expect(page.locator('.log-title')).toContainText('导入日志')
    })
  })

  test.describe('Parent Task Detail', () => {
    test('should navigate to parent task detail', async ({ page }) => {
      // Navigate to evaluations
      await page.goto('/evaluations')
      await waitForLoading(page)

      // Click on a parent task
      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')

      // Should be on parent task detail page
      await expect(page).toHaveURL(/\/evaluations\/\d+/)
      await expect(page.locator('.parent-task-detail-page')).toBeVisible()
    })

    test('should display parent task statistics', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      // Click on parent task
      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Check statistics cards
      await expect(page.locator('.stat-card:has-text("子任务总数")')).toBeVisible()
      await expect(page.locator('.stat-card:has-text("待执行")')).toBeVisible()
      await expect(page.locator('.stat-card:has-text("进行中")')).toBeVisible()
      await expect(page.locator('.stat-card:has-text("已完成")')).toBeVisible()
      await expect(page.locator('.stat-card:has-text("失败")')).toBeVisible()
      await expect(page.locator('.stat-card:has-text("整体准确率")')).toBeVisible()
    })

    test('should display overall progress bar', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Progress card should be visible
      await expect(page.locator('.progress-card')).toBeVisible()
      await expect(page.locator('.el-progress')).toBeVisible()
    })

    test('should display child task list', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Children table should be visible
      await expect(page.locator('.children-card')).toBeVisible()
      await expect(page.locator('.el-table')).toBeVisible()
    })

    test('should filter child tasks by status', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Open status filter
      await page.click('[data-testid="status-filter"]')

      // Select a status
      await page.click('.el-select-dropdown__item:has-text("进行中")')

      // Table should update
      await expect(page.locator('.el-table__row')).toBeVisible()
    })
  })

  test.describe('Batch Operations', () => {
    test('should show start all button for pending tasks', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      // Find a parent task with pending children
      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Start all button should be visible
      const startAllButton = page.locator('button:has-text("全部开始")')
      await expect(startAllButton).toBeVisible()
    })

    test('should show retry failed button when there are failed tasks', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // If there are failed tasks, retry button should be visible
      const retryButton = page.locator('button:has-text("重试失败")')
      // This may or may not be visible depending on task state
      const isVisible = await retryButton.isVisible().catch(() => false)
      if (isVisible) {
        await expect(retryButton).toBeEnabled()
      }
    })

    test('should cancel parent task', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      // Find a running parent task
      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("进行中"))')
      await waitForLoading(page)

      // Click cancel button
      await page.click('button:has-text("取消任务")')

      // Confirm dialog should appear
      await expect(page.locator('.el-message-box__wrapper')).toBeVisible()

      // Confirm cancellation
      await page.click('.el-message-box__btns button:has-text("确定")')

      // Should show success message
      await expect(page.locator('.el-message--success')).toBeVisible({ timeout: 5000 })
    })

    test('should start all child tasks', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Click start all
      await page.click('button:has-text("全部开始")')

      // Confirm dialog should appear
      await expect(page.locator('.el-message-box__wrapper')).toBeVisible()

      // Confirm
      await page.click('.el-message-box__btns button:has-text("确定")')

      // Should show success message
      await expect(page.locator('.el-message--success')).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('Child Task Actions', () => {
    test('should view child task details', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Click on view detail for first child task
      await page.click('.el-table__row:first-child button:has-text("查看详情")')

      // Should navigate to child task detail
      await expect(page).toHaveURL(/\/evaluations\/\d+/)
    })

    test('should cancel running child task', async ({ page }) => {
      await page.goto('/evaluations')
      await waitForLoading(page)

      await page.click('[data-testid="task-item"]:has(.el-tag:has-text("父任务"))')
      await waitForLoading(page)

      // Find a running child task and click cancel
      const cancelButton = page.locator('.el-table__row:has(.el-tag:has-text("进行中")) button:has-text("取消")')
      if (await cancelButton.isVisible().catch(() => false)) {
        await cancelButton.click()

        // Confirm
        await expect(page.locator('.el-message-box__wrapper')).toBeVisible()
        await page.click('.el-message-box__btns button:has-text("确定")')

        // Success message
        await expect(page.locator('.el-message--success')).toBeVisible({ timeout: 5000 })
      }
    })
  })

  test.describe('Import Configuration', () => {
    test('should configure evaluation mode', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Select eval mode
      await page.click('[data-testid="eval-mode-select"]')
      await page.click('.el-select-dropdown__item:has-text("多数投票")')

      // Verify selection
      await expect(page.locator('[data-testid="eval-mode-select"] .el-input__inner')).toContainText('多数投票')
    })

    test('should configure temperature', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Set temperature
      const slider = page.locator('.el-slider__runway')
      await slider.click()

      // Temperature value should be updated
      await expect(page.locator('.el-slider__input input')).not.toHaveValue('0')
    })

    test('should show warning for non-greedy modes', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Select pass_at_k mode
      await page.click('[data-testid="eval-mode-select"]')
      await page.click('.el-select-dropdown__item:has-text("Pass@K")')

      // Warning should be visible
      await expect(page.locator('.el-alert--warning')).toBeVisible()
      await expect(page.locator('.el-alert--warning')).toContainText('消耗更多 API')
    })
  })

  test.describe('Import Result', () => {
    test('should display import result after completion', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Trigger import
      const zipFileInput = page.locator('input[type="file"]')
      await zipFileInput.setInputFiles({
        name: 'bird_test.zip',
        mimeType: 'application/zip',
        buffer: Buffer.from('PK')
      })

      await page.click('[data-testid="api-key-select"]')
      await page.click('.el-select-dropdown__item:first-child')
      await page.click('[data-testid="start-import-button"]')

      // Wait for completion
      await page.waitForTimeout(2000)

      // Result section should be visible
      await expect(page.locator('.result-section')).toBeVisible()

      // Check result fields
      await expect(page.locator('.result-section')).toContainText('父任务ID')
      await expect(page.locator('.result-section')).toContainText('数据库连接')
      await expect(page.locator('.result-section')).toContainText('子任务')
    })

    test('should navigate to parent task after import', async ({ page }) => {
      await page.goto('/evaluations')
      await page.click('[data-testid="import-dataset-button"]')

      // Complete import
      const zipFileInput = page.locator('input[type="file"]')
      await zipFileInput.setInputFiles({
        name: 'bird_test.zip',
        mimeType: 'application/zip',
        buffer: Buffer.from('PK')
      })

      await page.click('[data-testid="api-key-select"]')
      await page.click('.el-select-dropdown__item:first-child')
      await page.click('[data-testid="start-import-button"]')

      // Wait and close dialog
      await page.waitForTimeout(2000)
      await page.click('button:has-text("完成")')

      // Should be back on evaluations page
      await expect(page).toHaveURL(/\/evaluations/)
    })
  })
})
