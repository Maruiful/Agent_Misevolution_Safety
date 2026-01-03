package com.agent.misevolution.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 停止实验请求
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class StopExperimentRequest {

    /**
     * 实验 UUID
     */
    private String experimentUuid;
}
