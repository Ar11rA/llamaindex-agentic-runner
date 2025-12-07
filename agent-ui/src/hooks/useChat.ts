import { useCallback, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import {
  addUserMessage,
  startAssistantMessage,
  setCurrentAgentName,
  appendToAssistantMessage,
  completeAssistantMessage,
  cancelStreaming,
  setHITLState,
  setError,
} from '../store/chatSlice';
import { streamChat, streamHITLResponse, startFlowAsync, pollFlowRun } from '../services/api';
import type { FlowStepStatus } from '../types';

// Get icon for step name
function getStepIcon(stepName: string): string {
  const icons: Record<string, string> = {
    research: '🔬',
    write: '✍️',
    critique: '🔍',
    rewrite: '📝',
    review: '👀',
    edit: '✏️',
    analyze: '📊',
    generate: '⚡',
    validate: '✅',
    process: '⚙️',
  };
  return icons[stepName.toLowerCase()] || '▶️';
}

// Get status icon
function getStatusIcon(status: string): string {
  switch (status.toLowerCase()) {
    case 'completed': return '✅';
    case 'running': return '⏳';
    case 'pending': return '⏸️';
    case 'rejected': return '🔄';
    case 'failed': return '❌';
    case 'skipped': return '⏭️';
    default: return '📌';
  }
}

// Format flow event for display (streaming mode)
function formatFlowEvent(eventType: string, data: Record<string, unknown>): string {
  const stepName = data.step_name as string | undefined;
  const details = data.details as string | undefined;
  const status = data.status as string | undefined;
  const eventData = data.data as Record<string, unknown> | undefined;

  if (eventType === 'StepStartedEvent') {
    const icon = stepName ? getStepIcon(stepName) : '▶️';
    const name = stepName ? capitalize(stepName) : 'Step';
    const info = details || 'Processing...';
    return `${icon} **${name}**: ${info}\n\n`;
  }

  if (eventType === 'StepCompleteEvent') {
    const icon = status ? getStatusIcon(status) : '✅';
    const name = stepName ? capitalize(stepName) : 'Step';
    
    let info = status ? capitalize(status) : 'Done';
    if (eventData) {
      const extras: string[] = [];
      if (eventData.research_length) extras.push(`${eventData.research_length} chars`);
      if (eventData.article_length) extras.push(`${eventData.article_length} chars`);
      if (eventData.score !== undefined) extras.push(`score: ${eventData.score}`);
      if (eventData.attempt) extras.push(`attempt ${eventData.attempt}`);
      if (eventData.action) extras.push(`→ ${eventData.action}`);
      if (extras.length > 0) {
        info += ` (${extras.join(', ')})`;
      }
    }
    
    return `${icon} **${name}**: ${info}\n\n`;
  }

  if (eventType === 'StopEvent') {
    const result = data.result as Record<string, unknown> | string;
    if (typeof result === 'string') {
      return `---\n\n${result}`;
    }
    if (result && typeof result === 'object' && 'article' in result) {
      return `---\n\n${result.article as string}`;
    }
    return `---\n\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\``;
  }

  return `📌 **${eventType}**\n\n`;
}

// Format step for async polling display
function formatAsyncStep(step: FlowStepStatus, isNew: boolean): string {
  const icon = getStepIcon(step.step_name);
  const statusIcon = getStatusIcon(step.status);
  const duration = step.duration_ms ? ` (${step.duration_ms}ms)` : '';
  
  if (isNew && step.status === 'running') {
    return `${icon} **${capitalize(step.step_name)}**: Running...\n\n`;
  }
  
  return `${statusIcon} **${capitalize(step.step_name)}**: ${capitalize(step.status)}${duration}\n\n`;
}

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// Sleep helper
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function useChat() {
  const dispatch = useAppDispatch();
  const { activeConversationId, conversations, selectedEntityId, selectedEntityType, flowMode, hitlState } =
    useAppSelector((state) => state.chat);

  const abortControllerRef = useRef<AbortController | null>(null);
  const pollingRef = useRef<boolean>(false);

  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!activeConversationId || !selectedEntityId || !activeConversation) {
        return;
      }

      // Add user message
      dispatch(addUserMessage({ conversationId: activeConversationId, content }));

      // Start assistant message
      dispatch(startAssistantMessage({ conversationId: activeConversationId }));

      // Create abort controller
      abortControllerRef.current = new AbortController();

      // Handle async mode for flows
      if (selectedEntityType === 'flow' && flowMode === 'async') {
        pollingRef.current = true;
        
        try {
          // Start the async flow
          const { run_id } = await startFlowAsync(selectedEntityId, {
            topic: content,
            session_id: activeConversation.sessionId,
          });

          dispatch(appendToAssistantMessage({
            conversationId: activeConversationId,
            content: `⏳ **Flow started** (run: \`${run_id.slice(0, 8)}...\`)\n\n`,
          }));

          // Poll for completion
          const lastStepStatuses: Record<string, string> = {};
          const pollInterval = 1500;

          while (pollingRef.current) {
            await sleep(pollInterval);

            // Check if cancelled
            if (!pollingRef.current) {
              dispatch(appendToAssistantMessage({
                conversationId: activeConversationId,
                content: '\n❌ **Cancelled**\n',
              }));
              break;
            }

            try {
              const runStatus = await pollFlowRun(selectedEntityId, run_id, true);

              // Show new or updated steps
              if (runStatus.steps) {
                for (const step of runStatus.steps) {
                  const stepKey = `${step.step_index}-${step.step_name}`;
                  const prevStatus = lastStepStatuses[stepKey];
                  
                  // Show step if it's new or status changed
                  if (!prevStatus || prevStatus !== step.status) {
                    const isNew = !prevStatus;
                    dispatch(appendToAssistantMessage({
                      conversationId: activeConversationId,
                      content: formatAsyncStep(step, isNew),
                    }));
                    lastStepStatuses[stepKey] = step.status;
                  }
                }
              }

              // Check completion
              if (runStatus.status === 'completed') {
                const result = runStatus.result;
                let resultText: string;
                
                if (typeof result === 'object' && result && 'article' in result) {
                  resultText = `---\n\n${(result as { article: string }).article}`;
                } else if (typeof result === 'string') {
                  resultText = `---\n\n${result}`;
                } else {
                  resultText = `---\n\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\``;
                }
                
                dispatch(appendToAssistantMessage({
                  conversationId: activeConversationId,
                  content: resultText,
                }));
                break;
              }

              if (runStatus.status === 'failed') {
                dispatch(appendToAssistantMessage({
                  conversationId: activeConversationId,
                  content: `\n❌ **Error**: ${runStatus.error || 'Unknown error'}\n`,
                }));
                break;
              }
            } catch (pollError) {
              // Network error during polling - log but continue
              console.error('Polling error:', pollError);
            }
          }

          dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
          return;

        } catch (error) {
          dispatch(appendToAssistantMessage({
            conversationId: activeConversationId,
            content: `\n❌ **Error**: ${error instanceof Error ? error.message : 'Failed to start flow'}\n`,
          }));
          dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
          return;
        } finally {
          pollingRef.current = false;
        }
      }

      // Streaming mode (for all entity types when not async)
      try {
        const stream = streamChat(
          selectedEntityId,
          selectedEntityType,
          content,
          activeConversation.sessionId,
          abortControllerRef.current.signal
        );

        for await (const event of stream) {
          if (event.type === 'token' && event.data) {
            dispatch(
              appendToAssistantMessage({
                conversationId: activeConversationId,
                content: event.data,
              })
            );
          } else if (event.type === 'agent' && event.agentName) {
            dispatch(setCurrentAgentName(event.agentName));
          } else if ((event.type === 'flow_event' || event.type === 'flow_result') && event.flowEvent) {
            const formatted = formatFlowEvent(event.flowEvent.eventType, event.flowEvent.data);
            dispatch(
              appendToAssistantMessage({
                conversationId: activeConversationId,
                content: formatted,
              })
            );
          } else if (event.type === 'hitl' && event.hitl) {
            dispatch(setHITLState(event.hitl));
            dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
            return;
          } else if (event.type === 'done') {
            dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
          } else if (event.type === 'hitl_pause') {
            return;
          }
        }

        dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          dispatch(cancelStreaming());
        } else {
          dispatch(setError(error instanceof Error ? error.message : 'Unknown error'));
          dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
        }
      } finally {
        abortControllerRef.current = null;
      }
    },
    [activeConversationId, selectedEntityId, selectedEntityType, flowMode, activeConversation, dispatch]
  );

  const respondToHITL = useCallback(
    async (response: string) => {
      if (!activeConversationId || !selectedEntityId || !hitlState) {
        return;
      }

      dispatch(startAssistantMessage({ conversationId: activeConversationId }));
      abortControllerRef.current = new AbortController();

      try {
        const stream = streamHITLResponse(
          selectedEntityId,
          selectedEntityType,
          {
            workflow_id: hitlState.workflowId,
            response,
          },
          abortControllerRef.current.signal
        );

        dispatch(setHITLState(null));

        for await (const event of stream) {
          if (event.type === 'token' && event.data) {
            dispatch(
              appendToAssistantMessage({
                conversationId: activeConversationId,
                content: event.data,
              })
            );
          } else if (event.type === 'agent' && event.agentName) {
            dispatch(setCurrentAgentName(event.agentName));
          } else if ((event.type === 'flow_event' || event.type === 'flow_result') && event.flowEvent) {
            const formatted = formatFlowEvent(event.flowEvent.eventType, event.flowEvent.data);
            dispatch(
              appendToAssistantMessage({
                conversationId: activeConversationId,
                content: formatted,
              })
            );
          } else if (event.type === 'hitl' && event.hitl) {
            dispatch(setHITLState(event.hitl));
            dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
            return;
          } else if (event.type === 'done') {
            dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
          } else if (event.type === 'hitl_pause') {
            return;
          }
        }

        dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          dispatch(cancelStreaming());
        } else {
          dispatch(setError(error instanceof Error ? error.message : 'Unknown error'));
          dispatch(completeAssistantMessage({ conversationId: activeConversationId }));
        }
      } finally {
        abortControllerRef.current = null;
      }
    },
    [activeConversationId, selectedEntityId, selectedEntityType, hitlState, dispatch]
  );

  const cancelStream = useCallback(() => {
    // Stop polling if active
    pollingRef.current = false;
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    dispatch(cancelStreaming());
    dispatch(setHITLState(null));
  }, [dispatch]);

  return {
    sendMessage,
    respondToHITL,
    cancelStream,
  };
}
