import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Card, CardContent, Typography, IconButton } from '@mui/material'
import DragHandleIcon from '@mui/icons-material/DragHandle'

export default function WidgetSortable({ widget, children, style }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: widget.id })

  const transformStyle = transform
    ? {
        transform: CSS.Transform.toString(transform),
        transition,
      }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={{
        ...style,
        ...transformStyle,
        opacity: isDragging ? 0.4 : 1,
        cursor: isDragging ? 'grabbing' : 'default',
      }}
    >
      <Card
        elevation={isDragging ? 8 : 2}
        sx={{
          borderRadius: 3,
          border: '1px solid #e8f5e9',
          background: '#fff',
          overflow: 'hidden',
          transition: 'box-shadow 0.2s, transform 0.15s',
          '&:hover': {
            boxShadow: isDragging ? 'none' : '0 4px 16px rgba(46,125,50,0.1)',
          },
        }}
      >
        {/* Drag Handle */}
        <div
          {...attributes}
          {...listeners}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 14px 4px',
            cursor: 'grab',
            userSelect: 'none',
          }}
        >
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 700, color: '#1b5e20', fontSize: '0.8rem' }}
          >
            {widget.title}
          </Typography>
          <IconButton size="small" sx={{ cursor: 'grab', color: '#9e9e9e' }}>
            <DragHandleIcon fontSize="small" />
          </IconButton>
        </div>

        {/* Widget Content */}
        <CardContent sx={{ p: '0 14px 14px !important', pt: 0 }}>
          {children}
        </CardContent>
      </Card>
    </div>
  )
}