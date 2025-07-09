# Daily Logger Assist - Frontend

A modern React frontend for the Daily Logger Assist application, built with TypeScript, Material-UI, and Redux Toolkit.

## Features

- **Authentication**: Login and registration with JWT tokens
- **Dashboard**: Overview of productivity metrics and recent activities
- **Work Items Management**: Create, edit, delete, and track work items
- **Reports & Analytics**: Interactive charts and productivity reports
- **Settings**: User profile and application preferences
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **React 19** with TypeScript
- **Material-UI (MUI)** for UI components
- **Redux Toolkit** for state management
- **React Router** for navigation
- **React Hook Form** with Yup validation
- **Recharts** for data visualization
- **Axios** for API communication

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- The backend microservices should be running (see main README)

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will be available at `http://localhost:3000`

### Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Auth/           # Authentication components
│   └── Layout/         # Layout and navigation
├── pages/              # Page components
│   ├── Auth/           # Login and registration pages
│   ├── Dashboard/      # Main dashboard
│   ├── WorkItems/      # Work items management
│   ├── Reports/        # Reports and analytics
│   └── Settings/       # User settings
├── services/           # API services
├── store/              # Redux store and slices
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

## API Integration

The frontend communicates with the microservices through the API Gateway. All API calls are centralized in the `services/api.ts` file and include:

- Authentication (login, register, token refresh)
- User management (profile, settings)
- Work items CRUD operations
- Reports generation and retrieval
- Notifications management

## State Management

The application uses Redux Toolkit with the following slices:

- **authSlice**: User authentication and profile data
- **workItemsSlice**: Work items state and operations
- **reportsSlice**: Reports and analytics data

## Styling

The application uses Material-UI (MUI) for consistent styling and theming. The theme is configured in `App.tsx` and can be customized for:

- Color palette
- Typography
- Component variants
- Responsive breakpoints

## Development

### Adding New Pages

1. Create a new component in the `pages/` directory
2. Add the route to `App.tsx`
3. Update the navigation in `Layout.tsx` if needed

### Adding New API Endpoints

1. Add the endpoint to the appropriate API service in `services/api.ts`
2. Create Redux actions if needed
3. Use the service in your components

### Styling Guidelines

- Use Material-UI components when possible
- Follow the established theme and spacing
- Ensure responsive design for mobile devices
- Use the `sx` prop for custom styling

## Building for Production

```bash
npm run build
```

The build output will be in the `build/` directory, ready for deployment.

## Docker

The frontend is containerized with Nginx for production deployment. See the `Dockerfile` and `nginx.conf` for configuration details.

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Ensure the backend services are running
2. **Authentication Issues**: Check JWT token storage and API endpoints
3. **Styling Issues**: Verify Material-UI version compatibility

### Development Tips

- Use React Developer Tools for debugging
- Check the browser console for API errors
- Use Redux DevTools for state debugging
- Test responsive design on different screen sizes

## Contributing

1. Follow the existing code structure and patterns
2. Use TypeScript for all new code
3. Add proper error handling and loading states
4. Test on different browsers and devices
5. Update documentation as needed
